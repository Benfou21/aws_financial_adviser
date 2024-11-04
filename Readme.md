
## App

This is a financial adiviser streamlit app.

### Features : 

- Select the ticker of the company you want to analyze from the top left.

- Just below, you can view the company’s latest report.

- Scrolling down the page, you’ll find additional useful information.

- You can ask questions about the company using the chatbot (the ticker is automatically added to the prompt, no need to specify the ticker).

- Last but not least, you can generate a complete analysis of the company by clicking the "Generate Analysis Report" button (this may take some  time; when finished, a new button to download the PDF will appear. If you wish to cancel the generation, select a new ticker).

- Look at rapport_AAPL.pdf to see an example of a generated report

### Access on EC2

- http://34.219.177.149/

### To Run locally

- pip -r install requirements.txt

- streamlit run app3.py

