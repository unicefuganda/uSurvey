##Explore uSurvey

###Roles in uSurvey: 

1.	Admin: Creates uSurvey Users and assigns them Roles
2.	Data Researcher: Creates and defines Modules, Groups, Listing, Survey and Questions. Also defines interviewers and assigns them to an Enumeration area to conduct survey 
3.	Interviewer: Conducts the actual survey on the field in designated enumeration area

Let us explore a sample Survey:

Survey has to be simplified to the Interviewer in identifying the household respondents, one who is eligible for this particular survey, based up on these Listing Questions and Grouping.

###Module: 
Is a high level classification of surveys Question types, based upon subject, are classified into Modules.
Ex: Household survey, School survey, etc

<b>Purpose</b>: Identity of a Survey.

<b>Precondition</b>: No dependency, can be created independently.

###Listing: 
Let us create a 'Listing' called ‘Public School’, once Listing is created then need to 'Add Questions' to the Listing, here the questions are differentiated into two types Looping and Non-looping questions.

Ex: Adding Questions in ‘Public School’ Listing (Looping and Non-looping questions)

1.	Do you have children? – Answer type is multiple type with Options Yes or No 
2.	How many children do you have? - Answer type is numeric
3.	What is the Age of 1st Child? - Answer type is numeric - <b>Start Loop</b> 
4.	Gender of 1st Child? - Answer type is multiple type with Options Male or Female 
5.	Does 1st Child going to School? - Answer type is multiple type with Options Yes or No 
6.	Which Class is 1st Child studying? - <b>End Loop</b>

From the above listing questions S. No. 1 and 2 are known as 'Non-looping' questions
and questions S. No. 3 to 6 are 'Looping' questions and also the concept of 'Start' and 'End' Loop arises here, which is based up on answer from Questions S. No. 2, therefore loop repetitions is done based on this numeric number.

###Groups: 

Groups are Survey dependent classification of people/respondents into one or more survey-taking categories.
Each group contains set of Variables, every Question is assigned to an identifier called ‘Variable’

Ex: Men, Women, Boys with age less than 18 years, etc

<b>Purpose</b>: To differentiate the people/ respondents, to apply logic and to set Questions.

<b>Precondition</b>: No dependency, can be created independently.

Let us create few Groups related to current Survey, 

1.	Single Moms
2.	Single Fathers
3.	Single member earning family

###Create a sample Survey:

Creating Survey means, one has to provide Survey Name, Description, survey type (Sampled or Census) and sample size of the survey and options like ‘Preferred Listing’ or ‘Listing Form’ and Groups are selected.

Preferred Listing: Is an option to choose, already conducted existing survey Listings in this New survey, which will integrate total survey Listing questions along with the data/results.

Listing Form: This will enable only if in the field ‘Preferred Listing’, option “None, Create New” is selected, and contains list of all Newly created Listings, which doesn’t participated in any survey.

Let us create a sample Survey known as 'The Educational Survey' related above Groups and Listing, i.e. as follows:

Name: The Educational Survey
Description: A Survey on Educational system.
Survey Type:  Sampled
Sample size: 5
Preferred Listing: None
Listing Form: Public School
Select Groups: "Single Moms, Single Fathers,	Single member earning family"

###Batches: 
Batches are set of Questions categorized for Survey convenience, let us create few Batches for our current Survey convenient. 
Once the Survey is created, one has to create ‘Batches’ and ‘Add Questions’ to each Batch as follows:
  
I. Batch Name: General</br>
   Questions in Batch: General</br>
   
1.	What is your Name?
2.	Are you the Head of the House?
3.	What is you Occupation?
4.	What is your Income?

II. Batch Name: Property</br>
   Questions in Batch: Property</br>
   
1.	Is this your own House?
2.	Do you have Agricultural Land?
3.	Do you have House other this?
4.	How many Houses you have?

Now, Survey: ‘The Educational Survey’ with Listing: ‘Public School’ and Groups: "Single Moms, Single Fathers, Single member earning family" and Batches: 'General' and 'Property' is created and ready.

Interviewer conducts the survey in the designated enumeration area, suppose an Interviewer is assigned to a survey know as ‘The Educational' Survey.




 
 
###Listing:
The Listing be carried out by field staff other than interviewers, as a separate field operation conducted before the survey starts.
It is the set of questions, each question is assigned to variable and these listings can be configurable/ reusable for any of the surveys.

<b>Purpose</b>: Reusability, looping of set Questions.

<b>Precondition</b>: No dependency, can be created independently.

Preferred Listing: Is an option to choose, already conducted existing survey Listings in this New survey, which will integrate total survey Listing questions along with the data/results.

Listing Form: This will enable only if in the field ‘Preferred Listing’, option “None, Create New” is selected, and contains list of all Newly created Listings, which doesn’t participated in any survey.


<b>Purpose</b>: to conduct a survey.

<b>Precondition</b>: dependency on Groups, Listing.


###Create a Survey: 
A new survey can be created and defined here, one has to provide Name, Description, survey type (Sampled or Census) and sample size of the survey and options like ‘Preferred Listing’ or ‘Listing Form’ and Groups are selected.


###New Interviewer: 
Interviewer registration is done, Token Name and Id are given and assigned to a Module and enumeration area to conduct survey.

<b>Purpose</b>: to conduct a survey.

<b>Precondition</b>:  dependency on Survey, enumeration area.



###Groups:

Grouping is available from main menu under <b>Survey Administration</b> >> <b>Groups</b>

Groups are Survey dependent classification of people/respondents into one or more Groups.
Each group contains set of Variables, every Question is assigned to an identifier called ‘Variable’

Grouping is available from main menu under Survey Administration >> Groups

The above Groups page is used to manage Groups, i.e. to Create a New Group, Edit existing Group, Delete Groups and Manage Variables

To Add a Variable, click on ‘Manage Variables’ button to view list of existing Variables and options to Add, Edit and Delete Variables

To Edit existing Group, every corresponding Group name has Actions column with Action items ‘Edit’ and ‘Delete’, select Edit to modify the Group.
   
 ![uSurvey map page](../screenshots/Map_groupZ_selected.png)

###Creating Groups:

Navigate to <b>Survey Administration</b> >> <b>Groups</b>

 ![Create Groups](../screenshots/Add_Groups.png)
 
The above Groups page is used to manage Groups, i.e. to Create a New Group, Edit existing Group, Delete Groups and Manage Variables.

###Manage Variables:

 click on ‘Manage Variables’ button to view list of existing Variables and options to Add, Edit and Delete Variables
 
 ![Manage Variables](../screenshots/addvariable.png)
 
###Add Variables:
 
 click on 'Add Variables' button, to navigare below show form. Where one can create new variable by assigning question. Provide 'variable Name' and Question in 'Text' feilds and select 'Answer' type.  
 
 ![Add Variables](../screenshots/Add_Variable.png)
 
 
###Edit Group:
 
 To Edit existing Group, every corresponding Group name has Actions column with Action items ‘Edit’ and ‘Delete’, select Edit to modify the Group.
 
 ![Edit Groups](../screenshots/Edit_group.png)

