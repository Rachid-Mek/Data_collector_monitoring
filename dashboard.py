import streamlit as st
import pandas as pd
from datetime import datetime
import base64
from Helpers import compute_entailment_score
from mongo import get_vector_counts, get_article_total_counts, get_daily_article_counts, get_qa

def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def highlight_rows(row):
    if row['upvote'] == 1:
        return ['background-color: #4DA760'] * len(row)
    elif row['downvote'] == 1:
        return ['background-color: #CE3030'] * len(row)
    elif row['flag'] == 1:
        return ['background-color: yellow'] * len(row)
    return ['background-color: black'] * len(row)

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

def sidebar():
    st.sidebar.title('Monitoring Dashboard')
    current_date = datetime.now().date()
    current_date_str = current_date.strftime('%Y-%m-%d')
    if 'view' not in st.session_state:
        st.session_state['view'] = 'Overtime'
    st.sidebar.markdown('---')

    if st.sidebar.button('General Info', use_container_width=True):
        st.session_state['view'] = 'Overtime'
    st.sidebar.markdown('---')
    
    if st.sidebar.button('Daily', use_container_width=True):
        st.session_state['view'] = 'Daily'
    st.sidebar.markdown('---')

    if st.sidebar.button('Q&A Tracking', use_container_width=True):
        st.session_state['view'] = 'QA'

    if st.session_state['view'] == 'Overtime':
        st.title('Database statistics for today :' + current_date_str)
        vector_counts_df = get_vector_counts()
        article_counts_df = get_article_total_counts()
        
        col1, col2 = st.columns(2)

        with col1:
            st.subheader('Article Counts')
            vectors_count_today = vector_counts_df[vector_counts_df['date'] == current_date_str]
            if not vectors_count_today.empty:
                st.success(f"Total number of articles today: {vectors_count_today['vector_count'].sum()}")
            else:
                st.success('No data available for the selected date.')

        st.markdown('---')

        with col2:
            st.subheader('Article Counts by source')
            article_counts_by_source = article_counts_df[article_counts_df['date'] == current_date_str]
            if not article_counts_by_source.empty:
                article_counts_by_source = article_counts_by_source.drop('date', axis=1).rename(columns={'nb_article': 'count'})
                st.dataframe(article_counts_by_source, use_container_width=True)
            else:
                st.warning('No data available for the selected date.')

        filtered_article_counts_df = article_counts_df[article_counts_df['date'] == current_date_str]
 
        st.subheader(f'Total Article Counts by Source')
        if not article_counts_df.empty:
            st.bar_chart(data=filtered_article_counts_df.set_index('source')['nb_article'], color='#ffaa00', use_container_width=True)
        else:
            st.warning('No data available for the selected date.')

        st.title('Statistics Overtime')
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Number of Articles Over Time")
            vector_counts_df = vector_counts_df.rename(columns={'vector_count': 'count'})
            st.dataframe(vector_counts_df, use_container_width=True)

        with col2:
            st.subheader('Total Article Count by Source')
            article_counts_df = article_counts_df.rename(columns={'nb_article': 'count'})
            st.dataframe(article_counts_df, use_container_width=True)

        st.subheader("Number of Articles Over Time")
        vector_counts_df['date'] = pd.to_datetime(vector_counts_df['date'])

        if not vector_counts_df.empty:
            st.line_chart(data=vector_counts_df.set_index('date')['count'], color='#ffaa00', use_container_width=True)
        else:
            st.write('No data available for articles over time.')

    elif st.session_state['view'] == 'Daily':
        st.title('Daily Article Counts')
        col1, col2 = st.columns(2)
        with col1:
            daily_articles_df = get_daily_article_counts()
            st.subheader(f'Article count for {current_date_str}')
            st.dataframe(daily_articles_df[daily_articles_df['date'] == current_date_str], use_container_width=True)

        with col2:
            st.subheader('Daily Article Counts')
            st.dataframe(daily_articles_df, use_container_width=True)

        article_counts_df = get_article_total_counts()
        selected_date = st.date_input('Select a date', datetime.now().date())
        article_counts_df['date'] = pd.to_datetime(article_counts_df['date'])
        selected_date_str = selected_date.strftime('%Y-%m-%d')

        daily_articles_df['date'] = pd.to_datetime(daily_articles_df['date'])
        daily_articles_df = daily_articles_df[daily_articles_df['date'] == selected_date_str]
        st.subheader(f'Barchart for daily article count for {selected_date}')
        if not daily_articles_df.empty:
            st.bar_chart(data=daily_articles_df.set_index('source')['count'])
        else:
            st.write('No data available for the selected date.')

        selected_source = st.selectbox('Select a source', article_counts_df['source'].unique())
        st.subheader(f'Number of Articles from {selected_source} Over Time')
        source_df = article_counts_df[article_counts_df["source"] == selected_source]

        if not source_df.empty:
            st.line_chart(data=source_df.set_index('date')['nb_article'])
        else:
            st.write(f'No data available for the selected source: {selected_source}')

    elif st.session_state['view'] == 'QA':
        st.title('Generation model\'s Q&A Tracking')
        qa_df = get_qa()
        total_votes = qa_df['upvote'].sum() + qa_df['downvote'].sum()
        if total_votes > 0:
            Accuracy = (qa_df['upvote'].sum() / total_votes) * 100
        else:
            Accuracy = 0
        qa_df = qa_df.apply(compute_entailment_score, axis=1)

        avg_entailment_score = qa_df[qa_df['Entailment'] > 0.2]['Entailment'].mean()
        number_of_flags = qa_df['flag'].sum()

        col1, col2, col3, col4 = st.columns(4)
        st.title('Q&A Tracking')
        with col1:
            st.subheader('Q&A Accuracy')
            if Accuracy < 50:
                st.error(f"{Accuracy:.2f}%")
            else:
                st.success(f"{Accuracy:.2f}%")
        with col2:
            st.subheader('Entailment Score')
            if avg_entailment_score < 0.5:
                st.error('{:.2f}'.format(avg_entailment_score))
            else:
                st.success('{:.2f}'.format(avg_entailment_score))
        with col3:
            st.subheader('Total Questions')
            st.success(f"Total Questions: {qa_df.shape[0]}")
        with col4:
            st.subheader('Number of Flags')
            if number_of_flags == 0:
                st.success('No flags reported')
            else:
                st.warning(f"Number of Flags: {number_of_flags}")
        
        st.dataframe(qa_df.style.apply(highlight_rows, axis=1))

        st.write('**Note:** Click on the expander to view the full question and answer.')
        for idx, row in qa_df.iterrows():
            with st.expander(f"Question: {row['question'][:50]}..."):
                st.write(f"**Question:** {row['question']}")
                st.write(f"**Answer:** {row['answer']}")
                st.write(f"**Upvotes:** {row['upvote']}")
                st.write(f"**Downvotes:** {row['downvote']}")
                st.write(f"**Flags:** {row['flag']}")
                st.write(f"**Timestamp:** {row['timestamp']}")
                st.write(f"**Entailment Score:** {row['Entailment']:.2f}")

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

st.set_page_config(page_title='Dashboard', page_icon=':bar_chart:', layout='wide')

st.markdown(custom_css, unsafe_allow_html=True)
set_png_as_page_bg('dash.png')

sidebar()