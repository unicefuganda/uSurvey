USSD Integration
================

uSurvey fully supports survey participation on USSD using the interactive menu capability of the USSD platform. To begin, from uSurvey portal, interviewers are sent SMS with details of the code to dial in order to commence data collection (e.g. *256#). The interviewer dials the code and then the survey starts.
  
![USSD Participation](./ussd-code-example.jpg)

What do I need to conduct survey on USSD?
-----------------------------------------------

1. Any mobile phone would do.
2. You need a USSD Aggregator.
3. You need to choose a mobile network which supports your chosen USSD Aggregator.
4. You need your chosen USSD Aggregator to forward USSD messages to uSurvey in the as follows:
    * Requests should be sent to as a HTTP GET or a POST to uSurvey USSD end point.
    * If you have hosted uSurvey with host IP `HOST_IP` and port `APP_PORT`, the USSD end point is `HTTP(s)://HOST_IP:APP_PORT/ussd`.
    * At a minimum, following parameters need to be sent to uSurvey USSD API from the aggregator:
        * `msisdn:` This parameter holds the mobile number of the responding interviewer.
        * `ussdRequestString:` This parameter holds the input string sent by the interviewer.
        * `transactionId:` This parameter holds the session ID of the USSD Interaction.
5. You to maintain connectivity to your mobile network (Since USSD participation requires an active USSD session).  
6. Now assign the interviewer to the relevant Survey and Enumeration area (for more info on this see the relevant section in the [User manual](./user_manual.md "#Interviewer Page"))
      