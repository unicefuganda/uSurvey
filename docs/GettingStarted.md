
###Getting Started

**The General flow for the uSurvey is as follows**:

* Admin creates uSurvey Users and assigns them Roles
* User ‘Data Researcher’ defines Modules, Groups, Listing, Surveys, Batches and creates questionnaires for Listing & Batches in application
* Data Researcher also defines ‘Interviewers’ and assigns them to an Enumeration area to conduct a Listing or Survey
* In the field, Interviewer conducts the actual survey in the designated Enumeration area
* Data collection is done using a hand-held mobile device like Android Smart Phone or Featured Phone via ODK and USSD channels respectively.
* Captured data is sent to uSurvey portal
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

3.0. Once Listing is created, next <br> 
3.1. Create Questions in Listing <br>
3.2. If necessary, <br>
3.3. Create Looping in questions and <br>
3.4. Add Logic to questions. <br>

**Step -4**

Create [New Survey](./Survey.md) or you can Clone existing Survey and rename it,<br>
**Clone existing Survey**: This option duplicates the survey along with the Listing data, and ready to use.

4.0. Once a new Survey is created, next <br>
4.1. Create Batch or Batches <br>
4.3. then Create Questions in Batch <br>
     If necessary, <br>
4.4. Create Looping in questions and <br> 
4.5. Add Logic to questions. <br>
4.6. Finally, don’t forget to change the status to Open, via Action Item ‘Open/Close’ for Batch

**Step -5**

Enroll [an Interviewer](./Interviewer.md) <br>
To conduct a Survey in the field, define an Interviewer as follows: <br>
5.0. Provide basic Interviewer details, <br>
5.1. Assign a Survey, <br>
5.2. Allocate Enumeration Areas, <br>
5.3. Create ODK Access ID, <br>
5.4. Provide Mobile Number to access via USSD channel <br>
5.5. Finally, finish enrollment <br>

**Step -6**

**Conduct Survey**: 
Data collection and submission is done in two ways:

1. Android channel - [Using uSurvey App](./ODK_App.md)
2. USSD channel - [Featured Phone](./ussd-integration.md)

At any point on the uSurvey portal, there are bread crumbs that makes navigation easy.
