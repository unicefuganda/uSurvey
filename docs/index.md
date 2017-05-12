Welcome to uSurvey’s documentation!
========
uSurvey is an innovative data collection tool designed to provide statistically representative real time estimates of a given indicator. It runs on USSD (Unstructured Supplementary Service Data) interactive secured channel and on ODK (Open Data Kit), for off-line data collection in locations with intermittent mobile network connections.

The system has been designed to collect a wide range of data for the structured survey; to generate and produce descriptive statistics and graphical representation of the collected information whenever desired, as well as during the process of data collection.
Source code for this project is available on github [here](https://github.com/unicefuganda/uSurvey/ "github repo").

###Features
------

* Admin management portal
* Classification of surveys using Modules
* Classification of population using Groups
* Highly customizable Listings and Surveys
* Preview questionnaire before go-live
* Offline data collection Using Smart Phone
* Online data collection Using Featured Phone
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

###Work Flow
------
Following are the simple steps to be executed in the given sequence, to ensure a Survey is completed.

######Step -1: Create a Module

Create [New Module](./User_Guides.md#modules) or skip this step, if you want to use existing Modules
######Step -2: Create a Group

Create [New Group](./User_Guides.md#groups) or skip this step, if you want to use existing Groups
######Step -3: Create a Listing 

In Listing, we have 3 choices as follows:

<dl>
<dd>3.0. Create <a href="./User_Guides/#listing">New Listing</a><br>
   &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp or <br>
         &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp Use existing Listing - Proceed to reuse Listing data collected already <br>  
   &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp or<br>
         &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp Clone existing Listing – Proceed to reuse Listing questions only<br>
</dd>
<dd>3.1. Create Questions in Listing</dd>
<dd>3.2. Create Looping in questions (If necessary)</dd>
<dd>3.3. Add Logic to questions (If necessary)</dd>
</dl>

######Step -4: Create a Survey

In Survey, we have 2 choices as follows:


<dl>
  <dd>4.0. Create <a href="./User_Guides/#create-survey">New Survey</a><br>
 &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp or <br>
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp Clone existing Survey and rename: Proceed to reuse the survey along with the Listing data and ready to use.<br>

</dd>
  <dd>4.1. Create Batch</dd>
  <dd>4.2. then Create Questions in Batch (If necessary)</dd>
  <dd>4.3. Create Looping in questions and</dd>
  <dd>4.4. Add Logic to questions</dd>
  <dd>4.5. Finally, enable <a href="./User_Guides/#enable-batch">Batch </a> for data collection, via Action Item ‘Open/Close’ for Batch</dd>
     Please note that Survey can not be downloaded on Mobile until this step is done
</dl>

######Step -5: Enroll Interviewer

To conduct a Survey in the field, enroll an [Interviewer](./User_Guides.md#interviewer) as follows:

<dl>
   <dd>5.0. Provide basic Interviewer details,</dd>
   <dd>5.1. Assign a Survey,</dd>
   <dd>5.2. Allocate Enumeration Areas,</dd>
   <dd>5.3. Create ODK Access ID,</dd>
   <dd>5.4. Provide Mobile Number to access via USSD channel</dd>
   <dd>5.5. Finally, finish enrollment</dd>
</dl>
Note: At any point on the uSurvey portal, use breadcrumbs on top of each page for easy navigation.

######Step -6: Conduct Survey

Data collection and submission is done in two ways:   
   
   1. Offline Data Collection - [Using Smart Phone](./ODK_App.md)
2. Online Data Collection  - [Using Featured Phone](./ussd-integration.md)   
   
###Complete List of User Guides
------
+ ######User Manual
    - [Modules](./User_Guides.md#modules)
    - [Groups](./User_Guides.md#groups)
    - [Listing](./User_Guides.md#listing)
    - [Survey](./User_Guides.md#create-survey)
    - [Question Library](./User_Guides.md#library-questions)
    - [Interviewers](./User_Guides.md#interviewer)
    - [Indicators](./User_Guides.md#indicators)
    - [Manage Users](./User_Guides.md#manage-users)
<pre>      </pre>
+ ######Data Collection
    - [Offline Data Collection](./ODK_App.md)
    - [Online Data Collection](ussd-integration.md)

+ ######Installation Guide
    - [Installation](installation.md)

+ ######Deployment Guide
    - [Application Architecture](deployment_guide.md)
  
+ ######Testing & Coverage
    - [Tests](tests.md)
