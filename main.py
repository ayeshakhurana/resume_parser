import streamlit as st
import spacy
import nltk
spacy.load('en_core_web_sm')
nltk.download('stopwords')
import importlib_metadata

import pandas as pd
import base64, random
import time, datetime

from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import PyPDF2

import pafy
import io, random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
import plotly.express as px
import youtube_dl
import yt_dlp

connection = pymysql.connect(host='localhost', user='root', password='ayesha',db='sra')
cursor = connection.cursor()

def get_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    x= f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return x

def fetch_video(vid):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(vid, download=False)
        return info_dict.get('title', 'Unknown Title')

def insert_data(name, email, resume_score, timestamp, page_no, level, skills, rskills, rcourses):
    skills = ', '.join(skills) if isinstance(skills, list) else skills
    rskills = ', '.join(rskills) if isinstance(rskills, list) else rskills
    rcourses = ', '.join(rcourses) if isinstance(rcourses, list) else rcourses

    insert_sql = """
    INSERT INTO user_data (name, email, resume_score, timestamp, page_no, level, skills, rskills, rcourses)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    try:
        cursor.execute(insert_sql, (name, email, resume_score, timestamp, page_no, level, skills, rskills, rcourses))
        connection.commit()
        print("Data inserted successfully!")
    except Exception as e:
        print(f"Error occurred while inserting data: {e}")
        connection.rollback()



def courserecommender(course):
    st.subheader("We recommend you to take the following courses to improve your skills and have a brighter resume: ")
    c=0
    x=st.slider("Choose the number of courses you want: ",1,10,4)
    rcourses=[]
    random.shuffle(course)
    for name,link in course:
        c+=1
        st.markdown(f"({c}) [{name}]({link})")
        if c==x:
            break
    return rcourses
    
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()
    converter.close()
    fake_file_handle.close()
    return text

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def run():
    st.title("RESUME ANALYSER")
    st.image('image.png', width=700)
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    
    connection = pymysql.connect(host='localhost', user='root', password='ayesha', db='sra')
    cursor = connection.cursor()
    db_sql = "CREATE DATABASE IF NOT EXISTS SRA;"
    cursor.execute(db_sql)
    connection.select_db("sra")
    
    DB_table_name = 'user_data'
    table_sql = """CREATE TABLE IF NOT EXISTS """ + DB_table_name + """
                    (id INT NOT NULL AUTO_INCREMENT,
                     name varchar(100) NOT NULL,
                     email VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     timestamp VARCHAR(50) NOT NULL,
                     page_no VARCHAR(5) NOT NULL,
                     level VARCHAR(50) NOT NULL,
                     skills TEXT NOT NULL,
                     rskills TEXT NOT NULL,
                     rcourses TEXT NOT NULL,
                     PRIMARY KEY (id));"""
    cursor.execute(table_sql)
    connection.commit()
    
    if choice == 'User':
        st.markdown('''<h5 style='text-align: left; color: white;'>Upload your resume, and get smart recommendation based on it.</h5>''', unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        
        if pdf_file is not None:
            with st.spinner('Analysing your resume...'):
                time.sleep(5)
            image_path = './input_resumes/' + pdf_file.name
            with open(image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(image_path)

            resumedata = ResumeParser(image_path).get_extracted_data()
            if resumedata:
                resumedata_text = pdf_reader(image_path)
                st.header("Greetings! ")             
                st.header("Resume Details")
                st.subheader("Details:- ")
                
                try:
                    st.text('Name: ' + resumedata['name'])
                    st.text('Email: ' + resumedata['email'])
                    st.text('Contact: ' + resumedata['mobile_number'])
                    st.text('Resume pages: ' + str(resumedata['no_of_pages']))
                except:
                    pass
                
                level = ''
                if resumedata['no_of_pages'] == 1:
                    level = "Fresher"
                elif resumedata['no_of_pages'] == 2:
                    level = "Intermediate"
                elif resumedata['no_of_pages'] >= 3:
                    level = "Experienced"
                
                st.text('Level: ' + level)
                
                st.header("Skills")
                keywords = st_tags(label='Key Skills:', text='Type and press enter', value=resumedata['skills'], key=1)

                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'c','c++','ai','machine learning', 'deep Learning', 'flask', 'streamlit']
                web_keyword = ['react', 'django', 'nodejs', 'react js','nextjs' 'php', 'laravel', 'mongodb', 'sql', 'javascript', 'angular js', 'c#', 'flask','api']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes', 'storyframes', 'adobe photoshop', 'photoshop']

                rskills = []
                rfield = ''
                rcourses = ''
                
                for i in resumedata['skills']:
                    if i.lower() in ds_keyword:
                        rfield = 'Data Science and Machine Learning'
                        st.success('Since you have skills in Data Science and Machine Learning, we recommend you to take the following courses to enhance your skills: ')
                        rskills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling', 'Data Mining', 'Clustering & Classification', 'Data Analytics', 'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras', 'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', 'Flask', 'Streamlit']
                        rcourses = courserecommender(ds_course)
                        break
                    elif i.lower() in web_keyword:
                        rfield = 'Web Development'
                        st.success('Since you have skills in Web Development, we recommend you to take the following courses to enhance your skills: ')
                        rskills = ['HTML', 'CSS', 'JavaScript', 'React.js', 'Vue.js', 'Angular', 'Node.js', 'Express.js', 'Django', 'Flask', 'Bootstrap', 'Tailwind CSS', 'SASS', 'Redux', 'Vuex', 'REST API', 'GraphQL', 'MySQL', 'MongoDB', 'PostgreSQL', 'Git', 'GitHub', 'Netlify', 'Vercel', 'Docker']
                        rcourses = courserecommender(web_course)
                        break
                    elif i.lower() in android_keyword:
                        rfield = 'Android Developer'
                        st.success('Since you have skills in Android Development, we recommend you to take the following courses to enhance your skills: ')
                        rskills = ['Java', 'Kotlin', 'XML', 'Android Studio', 'Gradle', 'Jetpack Compose', 'Firebase', 'SQLite', 'Room Database', 'Retrofit', 'Volley', 'REST API', 'MVVM', 'MVP', 'Data Binding', 'LiveData', 'Coroutines', 'Dagger Hilt', 'Koin', 'Git', 'GitHub']
                        rcourses = courserecommender(android_course)
                        break
                    elif i.lower() in ios_keyword:
                        rfield = 'iOS Developer'
                        st.success('Since you have skills in iOS Development, we recommend you to take the following courses to enhance your skills: ')
                        rskills = ['Swift', 'Objective-C', 'Xcode', 'Cocoa Touch', 'UIKit', 'Core Data', 'Core Animation', 'Core Graphics', 'Core Location', 'Core ML', 'ARKit', 'MapKit', 'Firebase', 'Alamofire', 'RxSwift', 'Combine', 'Git', 'GitHub']
                        rcourses = courserecommender(ios_course)
                        break
                    elif i.lower() in uiux_keyword:
                        rfield = 'UI/UX Designer'
                        st.success('Since you have skills in UI/UX Designing, we recommend you to take the following courses to enhance your skills: ')
                        rskills = ['Adobe XD', 'Figma', 'Sketch', 'InVision', 'Zeplin', 'Balsamiq', 'Wireframes', 'Prototyping', 'User Research', 'User Testing', 'User Flows', 'Adobe Illustrator', 'Adobe Photoshop', 'UI Design', 'UX Design', 'Interaction Design', 'Visual Design', 'Design Thinking', 'User-Centered Design', 'Responsive Design']
                        rcourses = courserecommender(uiux_course)
                        break
                
                ts = time.time()
                curtime = datetime.datetime.fromtimestamp(ts).strftime('%D-%m-%Y')
                curdate = datetime.datetime.fromtimestamp(ts).strftime('%H-%M-%S')
                timestamp = str(curdate + ' ' + curtime)

                st.subheader('Here\'s your resume score: ')
                score = 0
                if 'Education'  in resumedata_text:
                    score += 10
                    st.write('1.Great that you added Education in your resume.')
                else:
                    st.write('1. What\'s your education for this role? Go ahead and consider adding that in your resume.')
                if 'Objectives' or 'Goals' in resumedata_text:
                    score+=10
                    st.write('2. Great that you added Objectives in your resume.')
                else:
                    st.write('2. What\'s your objective for this role? Go ahead and consider adding that in your resume.')
                
                if 'Experience' or 'Work Experience'  in resumedata_text:
                    score += 20
                    st.write('3. Great that you added Experience in your resume.')
                else:
                    st.write('3. You should really gain some experiences in your field.')
                
                if 'Hobbies' or 'Interests' in resumedata_text:
                    score += 10
                    st.write('4. Great that you added Hobbies/Interests in your resume.') 
                else:
                    st.write('4. Don\'t you have any hobbies or interests? Go ahead and consider adding that in your resume.')
                if 'Skills' or 'SKILLS' in resumedata_text:
                    if(len(resumedata['skills']) > 15):
                        score+=5
                    else:
                        score+=10
                    st.write('5. Great that you added skills in your resume')
                else:
                    st.write('5.Consider adding some skills in your resume')
                
                if 'Projects' in resumedata_text:
                    score += 20
                    st.write('6. Great that you added Projects in your resume.')
                else:
                    st.write('6. Show your skills through projects and enhance your showcase.')

                if 'Achievements' in resumedata_text:
                    score +=20
                    st.write('7. Great that you added Achievements in your resume.')
                else:
                    st.write('7. Go out Achieve something and add that in your resume.')
                
                st.markdown("""<style>.stProgress > div > div > div > div { background-color: #d73b5c;}</style>""", unsafe_allow_html=True)
                bar = st.progress(0)
                for i in range(score):
                    bar.progress(i + 1)
                    time.sleep(0.1)
                st.success(f"Your resume score is: {score}")
                st.write(f"Your resume is {level} level resume.")

                insert_data(resumedata['name'], resumedata['email'], score, timestamp, resumedata['no_of_pages'], level, keywords, rskills, rcourses)

                st.subheader('Your resume has been successfully analysed and saved in our database.')
                st.write('Thank you for using our service here are some bonus recommendations for you: ')
                st.header('For Resume Enhancements:- ')
                resume_vid = random.choice(resume_videos)
                res_vid_title = fetch_video(resume_vid)
                st.subheader("✅ **" + res_vid_title + "**")
                st.video(resume_vid)

                st.header('For Interview Preperations:- ')
                interview_vid = random.choice(interview_videos)
                int_vid_title = fetch_video(interview_vid)
                st.subheader("✅ **" + int_vid_title + "**")
                st.video(interview_vid)

                connection.commit()
            else:
                st.error('Something went wrong..')
        
    elif choice == 'Admin':
        st.subheader("Admin Panel")
        user = st.text_input("Enter your username: ")
        password = st.text_input("Enter your password: ", type='password')
        if st.button("Login"):
            if user == 'ayeshakhurana' and password == 'bingo':
                st.success("Welcome Ayesha!")
                st.subheader("User Data")
                cursor.execute("SELECT * FROM user_data")
                data = cursor.fetchall()
                st.write('Here\'s your data:- ')
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Page No', 'Level', 'Skills', 'Recommended Skills', 'Recommended Courses'])
                st.dataframe(df)
                st.markdown(get_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)

                query = "SELECT * FROM user_data"
                plotdata = pd.read_sql(query, connection)

                if not plotdata.empty:
                    st.subheader('Pie Chart for Level Distribution:- ')
                    if 'level' in plotdata.columns:
                        level_distribution = plotdata['level'].value_counts()
                        fig = px.pie(
                            values=level_distribution.values, 
                            names=level_distribution.index, 
                            title='Levels according to the Skills'
                        )
                        st.plotly_chart(fig)
                    else:
                        st.error("Column 'Level' not found in the dataset.")

                    st.subheader('Pie Chart for Resume Score Distribution:- ')
                    if 'resume_score' in plotdata.columns:
                        score_distribution = plotdata['resume_score'].value_counts()
                        fig = px.pie(
                            values=score_distribution.values, 
                            names=score_distribution.index, 
                            title='Resume Score according to the Skills'
                        )
                        st.plotly_chart(fig)
                    else:
                        st.error("Column 'Resume Score' not found in the dataset.")
                else:
                    st.error("No data found in the database. Please add some entries.")
            else:
                st.error("Invalid Credentials! Please try again.")
    else:   
        pass




run()
print("Hello World")