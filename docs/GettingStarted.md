
###Getting Started

**The General flow for the uSurvey is as follows**:

* Admin creates uSurvey Users and assigns them Roles
* User ‘Data Researcher’ defines Modules, Groups, Listing, Surveys, Batches and creates questionnaires for Listing & Batches in application
* Data Researcher also defines ‘Interviewers’ and assigns them to an Enumeration area to conduct a Listing or Survey
* In the field, Interviewer conduct the actual survey in the designated Enumeration area
* Data collection is done using the hand-held mobile device like Android Smart Phone or Featured Phone via ODK and USSD channels respectively.
* Captured data is sent to uSurvey server
* Data collected by Interviewers is then viewed on the uSurvey portal for reporting and analysis

**A Quick step by step uSurvey process flow**

**Step -1**

Create [New Module](./Modules.md) or skip this step, if you want to use existing Modules

**Step -2**

Create [New Group](./Groups.md) or skip this step, if you want to use existing Groups

**Step -3**

Create [New Listing](./Listing.md) or skip this step, if you want to use existing Listing or you can Clone existing Listing and rename it. Here we have to observe two things;

1. Use existing Listing: This option benefits by providing data collected earlier <br>
2. Clone existing Listing: Duplicates Listing questions only <br>

Once Listing is created, next <br> 
Create Questions in Listing <br>
If necessary, <br>
Create Looping in questions and <br>
Add Logic to questions. <br>

**Step -4**

Create [New Survey](./Survey.md) or you can Clone existing Survey and rename it,<br>
**Clone existing Survey**: This option duplicates the survey along with the Listing data, and ready to use.

Once a new Survey is created, next <br>
Create Batch or Batches <br>
then Create Questions in Batch <br>
If necessary, <br>
Create Looping in questions and <br> 
Add Logic to questions. <br>
Finally, don’t forget to change the status to Open, via Action Item ‘Open/Close’ for Batch

**Step -5**

Enroll [an Interviewer](./Interviewer.md) <br>
To conduct a Survey in the field, define an Interviewer as follows <br>
Provide basic Interviewer details, <br>
Assign a Survey, <br>
Allocate Enumeration Areas, <br>
Create ODK Access ID, <br>
Provide Mobile Number to access via USSD channel <br>
Finally, finish enrollment <br>
