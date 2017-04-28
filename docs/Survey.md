###Create Survey

Surveys are available from main menu under **Design** >> **Surveys**
![Survey0](./Survey1.png)

A New Survey can be created and defined here, so before creating a survey first of all one has to know about the terminology used here.

* **Preferred Listing**: List of existing Listing, which are already in the system.<br>
Is an option to choose, existing Listing for this New Survey, where already survey was conducted on these Listings, which will include total Listing questions along with the data/results.

* **New Listing**: List of Newly created Listings, not previously used in any survey.<br>
This field will enable only if option “None, Create New” is selected, in the dropdown ‘Preferred Listing’. which contains list of Newly created Listings, which are not yet used in any survey.

* **Randomly selected data label**: Is the identifier for respondents while conducting a Listing survey.
  This field will enable only when listing in dropdown ‘New Listing’ is selected.

**How to create a Survey?**
To create a New Survey, click on ‘Create New Survey’ button at top right of the Survey page, that opens a form to create a new Survey, which has following elements;

![Survey1](./Survey2.png)

**Elements of a Survey**:

![Survey2](./Survey3.png)

* **Name**: Is Survey Name, which is a unique identity to a survey and is a mandatory field<br>
* **Description**: write about the importance of this survey in short<br>
* **Survey Type**: This identifies how survey is going to take place either using Listing or not<br>
    If Survey Type is “Sampled”, Survey uses Sample size and Listing<br>
    If Survey Type is “Census”, Survey doesn’t need Sample size and Listing

* **Sample size**: Provide survey sample size<br>
* **Preferred Listing**: select an existing Listing Or<br>
* **New Listing**: select Newly created Listing<br>
* **Randomly selected data label**: You need to include one listing response identifier in double curly brackets.<br>
 i.e. just type, double curly brackets to automatically insert ‘Variable Name’ in above selected Listing<br>
 Ex: type {{ , system prompts with ‘Variable Name’ then select any one to insert Variable Name<br>
 Like: {{house_number}} <br>
* **Email group**: select, User Emails Id to send report  

A New Survey is created by providing above fields and click on ‘Save’ button to Create a Survey. 

**Search**: One can find Surveys in the application, using the search bar at top right side of this survey page, by providing Name or description.

On the ‘Survey’ page one can view all the Survey created in the application, in a tabular form with following column names:

**Sts**: Represents Status of the Survey by color indicator, that means each of the Color code indicates as:
 <span style="color:Gray;font-weight:bold;">*</span>– Not Started<br>
 <span style="color:Orange;font-weight:bold;">*</span>– Ongoing<br>
 <span style="color:Green;font-weight:bold;">*</span>– Completed<br>

* **Name**: Is Name of a Survey, which is a unique identity to represent Survey and is a mandatory field.<br>
* **Description**: A short description about Listing<br>
* **Type**: Survey type Sampled or Census<br>
* **Sample size**: Provide survey sample size<br>
* **Total Respondents**: once the Survey is completed, this column will be updated with the count of participants/ respondents.<br>
* **Eas Covered**: Count of Enumeration areas covered in this particular survey.

**Actions in Survey**:

* **Edit Survey**: click on, Action Item ‘Edit’, User can Edit all fields in the Survey<br>
* **Delete Survey**: click on, Action Item ‘Delete, the entire Survey is removed, before deleting you will be prompted with conformation to delete, click ‘Yes’ to Delete permanently. <br> This option is not available for completed Survey<br>
* **View Batches in Survey**: click on, Action Item ‘View Batches’, navigates to ‘Survey Batches’ page<br>
* **Clone a Survey**: click on, Action Item ‘Clone’, an another copy of same Survey is created along with Survey Batches and Batch Questions, except existing Looping and Logic in Batch Questions<br>
* **Sampling Criteria**: 

###Batches
Batch is a categorization of Survey Questions, that means set of Questions categorized for a Survey convenience. We can create multiple Batches in a survey.

Once the Survey is created, next step is to create ‘Batch’ and ‘Add Questions’ to Batch.

**How to create a Batch?**

Go to Batches Page, which can be done in two ways
On the ‘Survey’ page you can view all the Survey created in the application
Now click on Survey Name, or click on, Action Item ‘View Batches’ to go to ‘Batches’ Page

To create a New Batch, click on ‘Create New Batch’ button at top right of the Batch page, that opens a form to create a new Batch, which has following elements;

**Elements of a Batch**:

* **Name**: Is Batch Name, which is a unique identity to a Batch and is a mandatory field<br>
* **Description**: write about the importance of this Batch in short<br>
* **Access channels**: This will identify on which channel this survey has to be conducted and has two channel ODK and USSD

A New Batch is created by providing above fields and click on ‘Save’ button to Create a New Batch in Survey. 

**Actions in Batch**:

* **Edit**: click on, Action Item ‘Edit’, User can Edit all fields in a Batch<br>
* **Delete**: click on, Action Item ‘Delete, the entire Batch along with questions are removed, before deleting you will be prompted with conformation to delete, click ‘Yes’ to Delete permanently. This option is not available for completed Surveys<br>
* **View/Edit Questions**: click on, Action Item ‘View /Edit Questions’, takes to the Survey ‘Batch Questions’ page <br>
* **Open/Close**: click on, Action Item ‘Open/Close’, takes to the page where all Enumeration Areas are listed, here one can change the “status of conducting survey in a particular Enumeration Area” to Open/Close<br>
i.e. Open- means allow to conduct survey and Close - means it prevents to conduct survey.

* **View Data**: click on, Action Item ‘View Data’, shows Data collected in this Survey. This option is available only for completed Surveys.

**How to create Batch Questions?**

Once Survey and Batches are created, next step is to ‘Add Questions’ to Batch as follows:

On the ‘Batch’ page you can view all the Batch created in a Survey
Now click on Batch Name, or click on, Action Item ‘View /Edit Question’ to go to ‘Batch Questions’ Page

Now click on, ‘Add Question’ button at top right side of this page, this will open a form where one can create a Question, which has following elements; 

**Elements in Batch Question form**:

* **Module**: All Modules in the application are listed here in this dropdown, one has to select, respective Module that is related to survey<br>
* **Group**: All available Groups are listed in this dropdown, select relevant group name for the question<br>
* **Variables Name**: This is an identifier for Question, type a code for Question<br>
* **Text**: Is the actual Question, Write a Question. While typing a question, auto suggestion feature is available, which will prompt with the ‘Variable Name’ of preceding questions, that helps to include “Answered text of preceding question” in framing this question. 
i.e. just type, double curly brackets to automatically prompt with the ‘Variable Name’ from preceding questions, <br>
Ex: type {{ , system prompts with ‘Variable Name’ then select any one to insert Variable Name,<br>
Like: {{structure_address}} <br>
* **Answer Type**: Select an Answer Type from dropdown list, such that Question has to be answered in any one of these formats only, that is ‘Answer type’ should be: “Audio, Auto Generate, Date, Geo Point, Image, Multi choice, Multi Select, Numeric, Text and Video”<br>
* **Mandatory**: To mark the Question, that has to answered compulsory

A Question in Batch is created by filling above all fields, finally click on ‘Save’ button to Add Question in Batch or click on ‘Save and Add More’ button to continue adding another Question to the same Batch or click on ‘Save and Update Library’ to add same to the ‘Questions Library’.

**Select Question**: On click, ‘Select Question’ button, User navigates to ‘Select Library Questions’ page where one can Add the Library Questions into Batch. 

To Add Question from Library to Batch, just Click on “Code” or “Text” to move Question between (Library Questions << / >> Batch Questions) tables, then click on ‘Save’ button at bottom of the page, to finish adding Questions to Batch.

**Search**: One can find Questions in Library by two ways:<br>
**Sort** questions using ‘Answer Type’ dropdown at top left side of this page Or<br>
**Search** using the search bar at top right side of this page, by providing text or code

**Export Questions**: On click, ‘Export Questions’ button, user can download the Batch Questions in “.csv” file format.

**Update Question Order**:<br>
Questions in the table can be rearranged.<br>
To change the order of the Question in table, just select the Question then drag (move up or down) and drop at new position/order you want to in the table, then click on ‘Update Question Order’ button at bottom of the Questions table.

On the ‘Batch Questions’ page one can view all the Questions created in that particular Batch, 

**Search**: One can find Questions in Batch by two ways:<br>
**Sort** questions using ‘Answer Type’ dropdown at top left side of this page Or<br>
**Search** using the search bar at top right side of this page, by providing text or code.

**Actions for Batch Questions**:

* **Edit Question**: click on, Action Item ‘Edit’, User can edit respective Question, ‘Variable Name’, ‘Text’ (Question), ‘Answer Type’ and can change ‘Mandatory’ type. This option is not available and cannot be performed for completed survey.

* **Insert Question**: click on, Action Item, ‘Insert Question’ using which User can insert a New Question below the respective Question and rest of the process is similar to ‘Add New Question’.

* **Delete Question**: click on, Action Item ‘Delete’, the Question is removed from list, before deleting you will be prompted with conformation to delete, click ‘Yes’ to Delete permanently.

Caution, while deleting a Question: when a user attempts to delete a question, if that particular question is assigned with Logic or Loop, then along with the question logic or entire loop is removed respectively.

**View Options**: This Action item is visible only for the Questions that has Answer Type “Multi choice” and “Multi Select”, to view Answer Options.

**Start/Edit Loop**:
‘Start/Edit Loop’ is an Action item available only for the Questions that has Answer Type “Auto Generated”. 

Looping means repeatedly asking set of questions based up the need and purpose of the base question.  

To define the Looping concept, first of all one has to understand about terms that are used in creating a Loop are as following:

**Repeat Logic**: To apply Looping for a question there should be some base criteria to start loop, that is chosen from ‘Repeat Logic’ as “User Defined”, “Fixed number of repeats” and “Response from previous question”

**User Defined**: Need to choose what set of Question come into loop, starting from this particular question and has to end loop with any of the consecutive question in the Batch.

**Fixed number of repeats**: Is chosen, need to provide ‘Repeat count’ – any specific no of times loop to be repeated. 

**Response from previous question**: Is chosen, only when a question that exists before this base question with Answer Type “Numerical Answer”. This logic is based up on numeric value provided in the previous question.

**Loop Ends At**: When a loop starts that has to be closed, here the choice at which question the loop as to be closed is selected.  

**Loop Prompt**: This is a message prompt shown on Mobile App during the time of capturing this details. This message will help the Interviewer to proceed further. 
Ex: “Do you what to Add one more”, “Do you what to Add another Household”, etc

###How to create a Loop?
<hr>

One should be very careful while creating a loop, first of all analyze how a loop has to be created, using ‘Repeat logic’ and where to ‘End Loop’, as defined above select accordingly from ‘Repeat logic’ and ‘Loop end at’ to define a loop.

* click on, Action Item ‘Start/Edit Loop’ which will take to ‘Start Loop’ page, now create loop as follows:<br>
* select “Logic Type” from dropdown ‘Repeat logic’,<br>
* select “Question at which loop should end” from dropdown ‘Loop end at’ and <br>
* in ‘Loop Prompt’ Text Box, write some message about, instructing the loop flow,<br>
* then click on ‘Save’ button to create loop.<br>
* Now you will be viewing a looping representation on ‘Batch Questions’ page in the ‘Code’ column of the ‘Questions’ table, 

**Loop Representation**:

* <span style="color:Chartreuse;font-weight:bold;"> | </span> - icon represents Loop - START,

* <span style="color:Red;font-weight:bold;"> | </span> - icon represents Loop - END,

* <span style="color:Green;font-weight:bold;"> | </span> - icon represents Loop - CONTINUATION

**Remove Loop**:

This Action item available only for the Questions that has Answer Type “Auto Generated” and a Loop is created.
click on, Action Item ‘Remove Loop’ which will remove the existing looping logic.

**Add Logic**: 

‘Add Logic’ is an Action item for every question expect for the Questions that has Answer Type “Auto Generated”.

Add Logic option will convert a question to conditional one such that question will have choices to “Reconfirm”, “End Interview”, “Ask Sub-Question” and “Skip To” which is based up on value/Answer provided.

One has to define the Logic here for respective question by satisfying the condition by providing ‘Eligible Criteria’, ‘Attribute’ Value, and ‘Then’ as follows:

**Eligible Criteria**: This is a condition made based up on this Question value “Starts With”, “Equals”, “Contains” and “Ends With”.

**Attribute**: Provide the “Value” as per the above ‘Eligible Criteria’ selected

**Then**: Based up on the ‘Eligible Criteria’ and ‘Attribute’ Value chosen, the condition for Question is applied here with following options:

**Reconfirm** – Prompts with conformation Question to validate the Answer 

**End Interview** – Skips the intermediate Question and moves to end of the questioner

**Ask Sub-Question** – Provides an option to Create a Sub-Question based upon the ‘Attribute’ value.<br>
To do this, select option “Ask Sub-Question” than you will find a button with name ‘Add Sub-Question’ beside this, 
click on it to create a Sub-Question, same like create question, once you click on ‘Save’ button, you will find this Sub-Question in the dropdown ‘Choose Question’ 
beside it, now select the “Sub-Question” and click on ‘Save’ button.
 
**Skip To** - Provides the option to jump to any particular/ consecutive question in the list, by skipping / avoiding the    intermediate Question. 

**How to Apply Logic to a Question?**

Click on, Action Item, ‘Add Logic’ this will open a form where one can create a Logic for Question, by providing ‘Eligible Criteria’, ‘Attribute’ Value, and ‘Then’ as per the condition required, then click on ‘Save’ button to create Logic.  

In the same page, logic that is created can be seen in table “Existing Logic”.
Which shows the created logic for this particular question and has option to ‘Delete’ the applied Logic

**Edit Logic**: 
In the ‘Batch Questions’ page, Questions that has Logic are represented with hyperlink, click on the respective Question, that shows options like ‘View logic’, ‘Edit’ and ‘Delete’

* **View Logic**: click to view the Logic that is Applied for this particular question <br>
* **Edit Logic**: click to Edit the existing Logic that is Applied for this particular question <br>
* **Delete Logic**: click to Remove the Logic that is Applied for this particular question