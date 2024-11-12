import streamlit as st
import pandas as pd
import re


#TOP OF APP
st.image("authormetrix_header_v00.jpg")
st.header ("Instructions")
st.markdown ("The app needs two *.csv* files as input for analysis. You need:  \n**(1.)** The relevant corpus downloaded from Scopus and,  \n**(2.)** The list of Scopus IDs of individuals that you need metrics for. <u> The Scopus IDs MUST be in the first column of the *.csv* file.</u>", unsafe_allow_html=True)


st.markdown("""<hr style="height:4px;border:none;color:#7F7F7F;background-color:#7F7F7F;" />""", unsafe_allow_html=True)

#STEP 1 STARTS
st.markdown ("### STEP 1")
st.markdown ("**Upload the corpus to be analyzed (*Scopus download*), from which authors' metrics will be obtained.**")
corpus_uploaded = st.file_uploader ("", type = [".csv"])  # Removed ".xlsx", ".xls" types for now, maybe I'll incorporate those later, just needs a few more lines of conditions

#Function to preprocess the uploaded corpus file
def preprocess_corpus (corpus_uploaded):
  corpus = pd.read_csv(corpus_uploaded)
  #Reducing the table to the bare essential columns, deduplication and general cleaning
  corpus ['Year'] = corpus ['Year'].astype(int)
  corpus01 = corpus[['EID', 'Author(s) ID', 'Title', 'Source title', 'Year', 'Document Type']]
  corpus01 = corpus01.drop_duplicates (subset = ['Author(s) ID', 'Title', 'Source title', 'Year'])
  corpus01 = corpus01.dropna(subset=['Author(s) ID', 'Document Type', 'Title', 'Year'])
  return corpus01

if corpus_uploaded is not None:
  st.write ("File uploaded successfully!")
  corpus01 = preprocess_corpus (corpus_uploaded)
  numberofdocs = len(corpus01)
  st.markdown (f"**UPDATE**: After removing duplicates and rows with missing information in essential columns, there are **<u>{numberofdocs}</u>** documents in the corpus.", unsafe_allow_html=True)
  #STEP 1 ENDS 
  
  st.markdown("""<hr style="height:4px;border:none;color:#7F7F7F;background-color:#7F7F7F;" />""", unsafe_allow_html=True)
  
  #STEP 2 STARTS: Optional user input to select document type and/or publication years to analyze
  st.markdown ("### STEP 2")
  st.markdown ("**OPTIONAL: Select <u>document type</u> and/or <u>publication year(s)</u> to include in the analysis.  \nDefaults are <u>Articles & Reviews</u>, and <u>all publication years</u> in the corpus, respectively.**", unsafe_allow_html=True)
  
  doctype = st.radio (label = "Document type", options= ['Articles & Reviews', 'All'])
  if doctype == 'Articles & Reviews':
    corpus01_doctype = corpus01.query('`Document Type`.isin(["Article", "Review"])')
  else:
    corpus01_doctype = corpus01

  Years = corpus01_doctype['Year'].unique()

  Years_selected = st.slider (label = "Drag the lower and upper end of the slider to set the range of publication years to include in the analysis.", min_value = min (Years), max_value = max (Years), value = (min (Years), max (Years)), step = 1)
  Years_selected = list(Years_selected)
  corpus01_doctype = corpus01_doctype [corpus01_doctype ['Year'].between(Years_selected[0], Years_selected[1])]
  doctype_Year_selection_lenght = len(corpus01_doctype)

  #I MAY OR MAY NOT KEEP THIS TABLE VISISBLE DEPENDING ON FEEDBACK
  #st.write (corpus01_doctype)
  start_year = min(Years_selected)
  end_year = max(Years_selected)
  st.markdown (f"**UPDATE**: You specified document type: <u>**{doctype}**</u>, and publication years: <u>**{start_year} to {end_year}**</u>.  \nThe number of documents in the specified corpus is <u>**{doctype_Year_selection_lenght}**</u>.", unsafe_allow_html=True)
  if st.button ("Preview pre-processed corpus"):
    st.write (corpus01_doctype)
  #STEP 2 ENDS
  
  st.markdown("""<hr style="height:4px;border:none;color:#7F7F7F;background-color:#7F7F7F;" />""", unsafe_allow_html=True)


  #STEP 3 STARTS
  st.markdown ("### STEP 3")
  st.markdown ("**Upload the csv file with the list of author Scopus IDs to be analysed. <u>IDs must be in the first column of the worksheet; only one ID per row.**</u>" ,unsafe_allow_html=True)
  IDs_list = st.file_uploader (".", type = [".csv"]) # Removed ".xlsx", ".xls" types for now, maybe I'll incorporate those later, just needs a few more lines of conditions

  #Function to further process corpus, to make columns needed to calculate the the author metrics.
  #I NEED TO CHECK WHETHER THERE IS A PROBLEM/POTENTIAL PROBLEM WITH MAKING THE STRIPPED FIRST_AUTHOR_ID AN INTEGER
  def corpus_preprocess_2 (corpus):
    corpus['author_ID_clean'] = corpus ['Author(s) ID'] + ';'
    corpus['authorcount'] = corpus['author_ID_clean'].str.count(';')
    corpus['fractional_credit'] = 1/corpus['authorcount']
    corpus['firstauthorid'] = corpus['author_ID_clean'].str.split(';').str.get(0).str.strip().apply(lambda x: int(x))
    return corpus

  #Function to prep the authors ID dataframe, then to extract first author IDs and to count total, and first author publications of the authors to analyze.
  def extract_publication_counts(corpus, scids_df):
    scids_df['all_publications'] = 0
    scids_df['first_author_publications'] = 0
  # Loop through scids
    for scid in scids_df['ID']:
        # Count matches in authorsid. Note the .astype(str) in the case of first author. This is because that column is currently a float data type
        pre_all = corpus['author_ID_clean'].str.contains(str(scid)).sum()
        pre_first = corpus['firstauthorid'].astype(str).str.contains(str(scid)).sum()
        # Update columns
        scids_df.loc[scids_df['ID']==scid, 'all_publications'] += pre_all
        scids_df.loc[scids_df['ID']==scid, 'first_author_publications'] += pre_first
    return scids_df 
  
  #Function to calculate the cummulative fractional output (CFO)
  def calculate_CFO (df_id, df_data):
    # Initialize the 'total_fractional_output' column with zeros
    df_id['total_fractional_output'] = 0
    # Loop through each ID in df_id
    for i in range(len(df_id)):
        id_value = str(df_id.loc[i, 'ID'])
        # Find rows in df_data where 'author_ID_clean' contains the ID
        mask = df_data['author_ID_clean'].str.contains(id_value, na=False)
        # Sum the 'score' for these rows
        total_score = df_data.loc[mask, 'fractional_credit'].sum()
        # Update the 'Appearances' column in df_id
        df_id.loc[i, 'total_fractional_output'] = total_score

    return df_id

  if IDs_list is not None:

    st.write ("File uploaded successfully!")
    IDs_list = pd.read_csv (IDs_list)
    #We need to rename the first column to 'ID' from whatever the user labelled it
    first_column = IDs_list.columns[0]
    IDs_list = IDs_list.rename(columns={first_column: 'ID'})
    #we also need to remove duplicates as I have found that this messes with results if an ID shows up more than once.
    IDs_list = IDs_list.drop_duplicates(subset =['ID'], keep='first')

    #Then we apply the functions to get the metrics
    corpus_preprocess_2 (corpus01_doctype)
    extract_publication_counts(corpus01_doctype, IDs_list)
    calculate_CFO (IDs_list, corpus01_doctype)
    #Calculate collaborative coefficient
    IDs_list['collaborative_coefficient'] = 1-(IDs_list['total_fractional_output']/IDs_list['all_publications'])
    #These lines clean up non-number characters from the cells, and makes sure that all numbers are to 4 decimal places 
    IDs_list['collaborative_coefficient'] = IDs_list['collaborative_coefficient'].round(4).astype('float')
    IDs_list['total_fractional_output'] = IDs_list['total_fractional_output'].round(4).astype('float')

    #st.write ("To download the authors' metrics, hover mouse on the top of the right corner of the table")
    if st.button ("Calculate and show authors' metrics!"):
      st.write (IDs_list)
      st.markdown ("***To download the authors' metrics, hover mouse on the top of the right corner of the table ↑***.")
st.markdown("""<hr style="height:4px;border:none;color:#7F7F7F;background-color:#7F7F7F;" />""", unsafe_allow_html=True)

st.markdown ("Thank you for using ***AuthormetriX***.  \n *Details of the metrics calculated in AuthormetriX are described in the accompanying publication(s). Kindly remember to cite. Full citation TBD; manuscript is being peer-reviewed.*",unsafe_allow_html=True)
st.markdown ("*Header generated by font-generator.com*")
