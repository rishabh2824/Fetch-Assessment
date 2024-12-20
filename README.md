The source code is available on the Master Branch.

To test the API, make sure you have Python installed. https://www.python.org/downloads/

Also make sure you have a suitable editor. https://code.visualstudio.com/docs/setup/windows

Once you have the environment setup, run the below commands in the IDE terminal:

```
pip install -r requirements.txt
```

Finally, you can test the API by sending requests! 
You can use a tool like Postman to send requests: https://www.postman.com/downloads/

Below are the Endpoints:

&emsp; Endpoint: http://127.0.0.1:8000/add

&emsp;&emsp; Method: POST

&emsp;&emsp; Description: Adds a transaction to the database. Expects JSON of the form:

&emsp;&emsp; {"payer" : "DANNON", "points" : 5000, "timestamp" : "2020-11-02T14:00:00Z"}

&emsp; Endpoint: http://127.0.0.1:8000/spend

&emsp;&emsp; Method: POST

&emsp;&emsp; Description: Spends a specified amount of points. Expects JSON of the form:

&emsp;&emsp; {"points" : 5000}

&emsp; Endpoint: http://127.0.0.1:8000/balance

&emsp;&emsp; Method: GET

&emsp;&emsp; Description: Get's the remaining balance for all payers


NOTE: The write up for the asssessment had contradicting information. In the instructions it said we have to return the payer names and the points subtracted for each payer in the spend endpoint. However, in the test case it said that we have to call the /balance endpoint. In my solution I have followed the original instructions.
