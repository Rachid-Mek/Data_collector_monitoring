import streamlit as st # Streamlit library for building web applications
import pandas as pd # Pandas library for data manipulation
from datetime import datetime # Datetime library for working with dates
import base64 # Base64 library for encoding and decoding binary data
from Helpers import compute_entailment_score # Helper function to compute the entailment score
from mongo import get_vector_counts, get_article_total_counts, get_daily_article_counts, get_qa # Import the functions to get the data from the MongoDB database

# the function to get the base64 encoding of a binary file
def get_base64(bin_file):
    with open(bin_file, 'rb') as f: # Open the binary file
        data = f.read() # Read the binary file
    return base64.b64encode(data).decode() # Return the base64 encoding of the binary file
# =============================================================================
# # the function to highlight the rows based on the upvote, downvote, and flag
def highlight_rows(row):
    if row['upvote'] == 1:
        return ['background-color: #4DA760'] * len(row)
    elif row['downvote'] == 1:
        return ['background-color: #CE3030'] * len(row)
    elif row['flag'] == 1:
        return ['background-color: lightyellow'] * len(row)
    return ['background-color: black'] * len(row)
# =============================================================================
# # the function to set the background image of the page
def set_png_as_page_bg(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)
# =============================================================================
# # the function to create the sidebar
def sidebar():
    st.sidebar.title('Monitoring Dashboard') # Set the title of the sidebar
    current_date = datetime.now().date() # Get the current date
    current_date_str = current_date.strftime('%Y-%m-%d') # Get the current date in the format YYYY-MM-DD
    if 'view' not in st.session_state: # Check if the view is not in the session state
        st.session_state['view'] = 'Overtime' # Set the view to Overtime
    st.sidebar.markdown('---') # Add a horizontal line

    if st.sidebar.button('General Info', use_container_width=True): # Add a button to switch to the General Info view
        st.session_state['view'] = 'Overtime' # Set the view to Overtime
    st.sidebar.markdown('---') # Add a horizontal line
    
    if st.sidebar.button('Daily', use_container_width=True): # Add a button to switch to the Daily view
        st.session_state['view'] = 'Daily' # Set the view to Daily
    st.sidebar.markdown('---') # Add a horizontal line

    if st.sidebar.button('Q&A Tracking', use_container_width=True): # Add a button to switch to the Q&A Tracking view
        st.session_state['view'] = 'QA' # Set the view to QA
# =============================================================================
    if st.session_state['view'] == 'Overtime': # Check if the view is Overtime
        st.title('Database statistics for today :' + current_date_str) # Set the title of the page
        vector_counts_df = get_vector_counts() # Get the vector counts
        article_counts_df = get_article_total_counts() # Get the article total counts
        
        col1, col2 = st.columns(2) # Create two columns

        with col1: # Add content to the first column
            st.subheader('Article Counts') # Set the subheader of the first column
            vectors_count_today = vector_counts_df[vector_counts_df['date'] == current_date_str] # Get the vector counts for today
            if not vectors_count_today.empty: # Check if the vector counts for today is not empty
                # st.dataframe(vectors_count_today, use_container_width=True) # Show the vector counts for today
                st.success(f"Total number of articles today: {vectors_count_today['vector_count'].sum()}") # Show the total number of articles for today
            else:
                st.success('No data available for the selected date.') # Show a success message if there is no data available for the selected date

        st.markdown('---') # Add a horizontal line

        with col2: # Add content to the second column
            st.subheader('Article Counts by source') # Set the subheader of the second column
            article_counts_by_source = article_counts_df[article_counts_df['date'] == current_date_str] # Get the article counts by source for today
            if not article_counts_by_source.empty: # Check if the article counts by source for today is not empty
                article_counts_by_source = article_counts_by_source.drop('date', axis=1).rename(columns={'nb_article': 'count'}) # Drop the date column and rename the nb_article column to count
                st.dataframe(article_counts_by_source, use_container_width=True) # Show the article counts by source for today
            else:
                st.warning('No data available for the selected date.') # Show a warning message if there is no data available for the selected date

        filtered_article_counts_df = article_counts_df[article_counts_df['date'] == current_date_str] # Filter the article counts by date
 
        st.subheader(f'Total Article Counts by Source') # Set the subheader for the total article counts by source
        if not article_counts_df.empty: # Check if the article counts by source is not empty
            st.bar_chart(data=filtered_article_counts_df.set_index('source')['nb_article'], color='#ffaa00', use_container_width=True) # Show the total article counts by source
        else:
            st.warning('No data available for the selected date.') # Show a warning message if there is no data available for the selected date

        st.title('Statistics Overtime') # Set the title of the page
        col1, col2 = st.columns(2) # Create two columns
        
        with col1:
            st.subheader("Number of Articles Over Time") # Set the subheader for the number of articles over time
            vector_counts_df = vector_counts_df.rename(columns={'vector_count': 'count'}) # Rename the vector_count column to count
            st.dataframe(vector_counts_df, use_container_width=True) # Show the number of articles over time

        with col2:
            st.subheader('Total Article Count by Source') # Set the subheader for the total article count by source
            article_counts_df = article_counts_df.rename(columns={'nb_article': 'count'}) # Rename the nb_article column to count
            st.dataframe(article_counts_df, use_container_width=True) # Show the total article count by source

        st.subheader("Number of Articles Over Time") # Set the subheader for the number of articles over time
        vector_counts_df['date'] = pd.to_datetime(vector_counts_df['date']) # Convert the date column to datetime

        if not vector_counts_df.empty: # Check if the vector counts dataframe is not empty
            st.line_chart(data=vector_counts_df.set_index('date')['count'], color='#ffaa00', use_container_width=True) # Show the number of articles over time
        else: # If the vector counts dataframe is empty
            st.write('No data available for articles over time.') # Show a message that there is no data available for articles over time
# =============================================================================
    elif st.session_state['view'] == 'Daily': # Check if the view is Daily
        st.title('Daily Article Counts') # Set the title of the page
        col1, col2 = st.columns(2) # Create two columns
        with col1: # Add content to the first column
            daily_articles_df = get_daily_article_counts() # Get the daily article counts
            st.subheader(f'Article count for {current_date_str}') # Set the subheader for the daily article count
            st.dataframe(daily_articles_df[daily_articles_df['date'] == current_date_str], use_container_width=True) # Show the daily article count for the current date

        with col2:
            st.subheader('Daily Article Counts') # Set the subheader for the daily article counts
            st.dataframe(daily_articles_df, use_container_width=True) # Show the daily article counts

        article_counts_df = get_article_total_counts() # Get the article total counts
        selected_date = st.date_input('Select a date', datetime.now().date()) # Add a date input to select a date
        article_counts_df['date'] = pd.to_datetime(article_counts_df['date']) # Convert the date column to datetime
        selected_date_str = selected_date.strftime('%Y-%m-%d') # Get the selected date in the format YYYY-MM-DD

        daily_articles_df['date'] = pd.to_datetime(daily_articles_df['date']) # Convert the date column to datetime
        daily_articles_df = daily_articles_df[daily_articles_df['date'] == selected_date_str] # Filter the daily articles by the selected date
        st.subheader(f'Barchart for daily article count for {selected_date}') # Set the subheader for the barchart for daily article count
        if not daily_articles_df.empty: # Check if the daily articles dataframe is not empty
            st.bar_chart(data=daily_articles_df.set_index('source')['count']) # Show the barchart for daily article count
        else: # If the daily articles dataframe is empty
            st.write('No data available for the selected date.') # Show a message that there is no data available for the selected date

        selected_source = st.selectbox('Select a source', article_counts_df['source'].unique()) # Add a selectbox to select a source
        st.subheader(f'Number of Articles from {selected_source} Over Time') # Set the subheader for the number of articles from the selected source over time
        source_df = article_counts_df[article_counts_df["source"] == selected_source] # Filter the article counts by the selected source

        if not source_df.empty: # Check if the source dataframe is not empty
            st.line_chart(data=source_df.set_index('date')['nb_article']) # Show the number of articles from the selected source over time
        else:
            st.write(f'No data available for the selected source: {selected_source}') # Show a message that there is no data available for the selected source
# =============================================================================
    elif st.session_state['view'] == 'QA': # Check if the view is QA
        st.title('Generation model\'s Q&A Tracking ') # Set the title of the page
        qa_df = get_qa() # Get the Q&A data
        total_votes = qa_df['upvote'].sum() + qa_df['downvote'].sum() # Compute the total votes
        if total_votes > 0: # Check if the total votes is greater than 0
            Accuracy = (qa_df['upvote'].sum() / total_votes) * 100  # Compute the accuracy
        else:
            Accuracy = 0 # Set the accuracy to 0 if the total votes is 0
        qa_df = qa_df.apply(compute_entailment_score, axis=1) # Compute the entailment score
        # avg_entailment_score = qa_df['Entailment'].mean() # Compute the average entailment score
        # compute mean for values that are >0.2
        avg_entailment_score = qa_df[qa_df['Entailment'] > 0.2]['Entailment'].mean() # Compute the average entailment score for values that are greater than 0.2
        number_of_flags = qa_df['flag'].sum() # Compute the number of flags

        col1, col2, col3, col4 = st.columns(4) # Create four columns
        st.title('Q&A Tracking') # Set the title of the page
        with col1: 
            st.subheader('Q&A Accuracy') # Set the subheader for the Q&A accuracy score
            if Accuracy < 50: # Check if the accuracy is less than 50
                st.error(f"{Accuracy:.2f}%") # Show an error message if the accuracy is less than 50
            else: 
                st.success(f"{Accuracy:.2f}%") # Show a success message if the accuracy is greater than or equal to 50
        with col2:
            st.subheader('Entailment Score') # Set the subheader for the entailment score
            if avg_entailment_score < 0.5: # Check if the average entailment score is less than 0.5
                st.error('{:.2f}'.format(avg_entailment_score)) # Show an error message if the average entailment score is less than 0.5
            else: # If the average entailment score is greater than or equal to 0.5
                st.success('{:.2f}'.format(avg_entailment_score)) # Show a success message
        with col3:  # Add content to the third column
            st.subheader('Total Questions') # Set the subheader for the total questions
            st.success(f"Total Questions: {qa_df.shape[0]}") # Show the total questions
        with col4: # Add content to the fourth column
            st.subheader('Number of Flags') # Set the subheader for the number of flags
            if number_of_flags == 0: 
                st.success('No flags reported') # Show a success message if there are no flags reported
            else: 
                st.warning(f"Number of Flags: {number_of_flags}") # Show a warning message if there are flags reported
        
        st.dataframe(qa_df.style.apply(highlight_rows, axis=1)) # Show the Q&A data with highlighted rows

        st.write('**Note:** Click on the expander to view the full question and answer.') # Show a note to click on the expander to view the full question and answer
        for idx, row in qa_df.iterrows(): # Iterate over the Q&A data
            with st.expander(f"Question: {row['question'][:50]}..."): # Add an expander for the question
                st.write(f"**Question:** {row['question']}") # Show the question
                st.write(f"**Answer:** {row['answer']}") # Show the answer
                st.write(f"**Upvotes:** {row['upvote']}") # Show the upvotes
                st.write(f"**Downvotes:** {row['downvote']}")  # Show the downvotes         
                st.write(f"**Flags:** {row['flag']}") # Show the flags
                st.write(f"**Timestamp:** {row['timestamp']}") # Show the timestamp
                st.write(f"**Entailment Score:** {row['Entailment']:.2f}") # Show the entailment score
# =============================================================================
# # the custom css for the page
custom_css = """
<style>
    .stButton>button {
        background-color: #745423;
        color: white;
    }
    .css-1d391kg {
        background-color: #20b2aa;
    }
    div[role="button"] > div:first-child {
        background-color: black !important;
        color: white !important;
    }
    div[role="region"] {
        background-color: black !important;
        color: black !important;
    }
</style>
"""
# =============================================================================
# # Set the page configuration
st.set_page_config(page_title='Dashboard', page_icon=':bar_chart:', layout='wide')

st.markdown(custom_css, unsafe_allow_html=True) # Apply the custom css to the page
set_png_as_page_bg('dash.png') # Set the background image of the page

sidebar() # Create the sidebar
# =============================================================================