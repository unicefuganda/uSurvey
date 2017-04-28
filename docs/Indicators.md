###Indicators

Survey Indicators, which forecast statistical metrics of data collection done in a survey individually.

Our system facilitates creating customized Indicators for every survey and show an analysis report in tabular and bar chart form.

**How to create an Indicator?**

On the ‘Indicator’ page one can view list of all survey wise Indicators in the application and can view analysis report.

To create an Indicator, click on ‘Add Indicator’ button at top right of the Indicator page, this will open a blank form with following elements;

**Elements in the Indicator form**

**Survey**: Select Survey from list, for which the Indicator need to be defined.

**Listing**: Select respective Listing, for which the Indicator need to be defined.

**Indicator**: Define a name to the Indicator   

**Description**: A short description about Indicator
 
**Variables**: To create an Indicator, certain metrics are needed for calculation, which are derived from survey/ listing questions   

**Formulae**: compose a formula based up on available Variables, <br>
Auto suggestion feature is available, which will prompt with the ‘Variables’ already defined above for composing. <br>
i.e. just type, double curly brackets to automatically prompt with the ‘Variables’ already defined, <br>
Ex: type {{ , system prompts with ‘Variables’ then select any one to insert Variable, <br>
Like: {{hh_age}} <br>

**Display on dashboard**: This option allows, this particular indicator to display on dashboard, as dashboard facilitates to display maximum five indicator.

**Add Variable**: 

To Add a Variable, click on respective ‘+’ icon adjacent to ‘Variables’ Text box, that opens form to define a Variable, following parameters are involved and expressed.

**Name**: Define a name to the Variable

**Description**: A short description about Variable

**Test question**: Select respective Listing questions, for which the Variable need to be defined.

**Operator**: Select respective operator based up on the value of the above ‘Test question’

Once all the above fields are filled, then click on ‘Add’ button to add to below table ‘Settings for this Variable’, since you can add more Variables for combination, once all Variables are defined then, finally click on ‘Save’ button to add to Variables list.

One can also ‘Edit’ and ‘Delete’ Variables using the respective icons adjacent to ‘Variables’ Text box.

Once Variables are defined, now you can compose the formula in ‘Formulae’ Text box, the composed formula is validated automatically and a message is shown here as ‘Valid’ or ‘in valid’.

Once Variables are defined, formula is composed and validated, finally click on ‘Save’ button to create an Indicator.

On the ‘Indicator’ page one can view all the Indicator created in the application, in a tabular form with following column names:

**Sts**: Represents Indicator display status on dashboard, that means status with color code indicates as:

 <span style="color:Gray;font-weight:bold;">•</span> – Not Displayed<br>
 <span style="color:Green;font-weight:bold;">•</span> – Displayed<br>

**Indicator**: Is the title of Indicator, which is a unique identity to represent Indicator of a Survey.

**Description**: A short description about Indicator

**Survey**: Name of the Survey to which this Indicator belongs

**Batch**: Name of the Survey Batch to which this Indicator belongs

**Actions**: 

* **Edit**: click on, Action Item ‘Edit’, User can Edit all fields in Indicator.
* **Delete**: click on, Action Item ‘Delete’, the Indicator is removed, before deleting you will be prompted with conformation to delete, click ‘Yes’ to Delete permanently
* **Formula**: click on, Action Item ‘Formula’, to edit the Indicator Formula directly
* **Analysis**: click on, Action Item ‘Analysis’, navigates to ‘Indicator Analysis’ page, here one can view two forms of district wise reports based up on the Indicator Formula,
  * A Bar chart report is generated and displayed
  * A tabular report 
