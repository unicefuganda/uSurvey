Welcome to uSurvey’s documentation!
========
uSurvey is an innovative data collection tool designed to provide statistically representative real time estimates of a given indicator. It runs on USSD (Unstructured Supplementary Service Data) interactive secured channel and on ODK (Open Data Kit), for off-line data collection in locations with intermittent mobile network connections.

The system has been designed to collect a wide range of data for the structured survey; to generate and produce descriptive statistics and graphical representation of the collected information whenever desired, as well as during the process of data collection.
Source code for this project is available on github [here]()

###Features
------
* Admin management portal
* Classification of surveys using Modules
* Classification of population using Groups
* Highly customizable Listings and Surveys
* Preview questionnaire before go-live
* Offline data collection via USSD channel
* Online data collection via uSurvey App
* Download, search and edit submitted forms in uSurvey App
* Country Map is used to demonstrate district wise Completion rates and Indicators 
* Customizable Indicators to measure survey results
* Configurable data analysis reports generation

###Getting Started
------
**General flow of the uSurvey**:

* Admin creates uSurvey Users and assigns them Roles
* User ‘Data Researcher’ defines Modules, Groups, Listing, Surveys, Batches and creates questionnaires for Listing & Batches in application
* Data Researcher also defines ‘Interviewers’ and assigns them to an Enumeration area to conduct a Listing or Survey
* In the field, Interviewer conducts the actual survey in the designated Enumeration area
* Data collection is done using a hand-held mobile device like Android Smart Phone or Featured Phone via ODK and USSD channels respectively.
* Captured data is sent to uSurvey portal
* Data collected by Interviewers is then viewed on the uSurvey portal for reporting and analysis

###Glimpse of uSurvey 
------
#####Step -1: Create Module

Create [New Module](./User_Guides.md#modules) or skip this step, if you want to use existing Modules
#####Step -2: Create Group

Create [New Group](./User_Guides.md#groups) or skip this step, if you want to use existing Groups

#####Step -3: Create Listing 

Create [New Listing](./User_Guides.md#listing) or skip this step, if you want to use existing Listing or you can Clone existing Listing and rename it. Here we have to observe two things;

* Use existing Listing: This option benefits by providing data collected earlier
* Clone existing Listing: Duplicates Listing questions only

  3.0. Once Listing is created, next <br> 
  3.1. Create Questions in Listing <br>
  3.2. If necessary, <br>
  3.3. Create Looping in questions and <br>
  3.4. Add Logic to questions. <br>

#####Step -4: Create Survey

Create [New Survey](./User_Guides.md#create-survey) or you can Clone existing Survey and rename it,<br>
**Clone existing Survey**: This option duplicates the survey along with the Listing data, and ready to use.

  4.0. Once a new Survey is created, next <br>
  4.1. [Create Batch](./User_Guides.md#batches) <br>
  4.3. then Create Questions in Batch <br>
     If necessary, <br>
  4.4. Create Looping in questions and <br> 
  4.5. Add Logic to questions. <br>
  4.6. Finally, don’t forget to change the status to Open, via Action Item ‘Open/Close’ for Batch

#####Step -5: Enroll Interviewer

Enroll [an Interviewer](./User_Guides.md#interviewer) <br>
To conduct a Survey in the field, define an Interviewer as follows: <br>
 5.0. Provide basic Interviewer details, <br>
 5.1. Assign a Survey, <br>
 5.2. Allocate Enumeration Areas, <br>
 5.3. Create ODK Access ID, <br>
 5.4. Provide Mobile Number to access via USSD channel <br>
 5.5. Finally, finish enrollment <br>

#####Step -6: Conduct Survey

Data collection and submission is done in two ways:

1. Android channel - [Using uSurvey App](./ODK_App.md)
2. USSD channel - [Using Featured Phone](./ussd-integration.md) <br>
At any point on the uSurvey portal, use breadcrumbs on top of each page for easy navigation.

###User Guides
------
+ **Administration Guide**
    - [Modules](./User_Guides.md#modules)
    - [Groups](./User_Guides.md#groups)
    - [Listing](./User_Guides.md#listing)
    - [Survey](./User_Guides.md#create-survey)
    - [Question Library](./User_Guides.md#library-questions)
    - [Interviewers](./User_Guides.md#interviewer)
    - [Indicators](./User_Guides.md#indicators)


* **Online Data Collection**
    - [uSurvey App](./ODK_App.md)


* **Offline Data Collection**
    - [USSD](ussd-integration.md)


* **Installation Guide**
    - [Installation](installation.md)


* **Deployment Guide**
    - [Application Architecture](deployment_guide.md)


* **Testing & Coverage**
    - [Tests](tests.md)
