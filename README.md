# Quantum Ready Solution For Drug Discovery

## How to use?

1. Signup for QuickSight
   - Go to [quicksight](https://quicksight.aws.amazon.com/sn/start)
   - Click "Sign uup for QuickSight"
   - Choose `Enterprise`, click continue
   - In the `Create your QuickSight account` page, fill the necessary infomaiton:
   ![create quicksight](./docs/images/create_quicksight.png) 
   - Go to [quicksight admin](https://us-east-1.quicksight.aws.amazon.com/sn/admin), record your QuickSight username
   ![quicksight username](./docs/images/quicksight_username.png)    

2. Create `cdk.context.json`

```shell
cd source
cp cdk.context.template.json cdk.context.json 

# edit cdk.context.json, 
# fill  `quicksight_user` in step 1, 
# fill `quicksight_template_account_id` from user guide.

```

3. Deploy 

```shell
cd source

npm install
npm run deploy

```

4. After deployment, go to [cloudformation](https://console.aws.amazon.com/cloudformation/home), find the statck `QCStack`, from the output, you will get related links for Notebook, stepFunctions to run benchmark tasks, and QuickSight dashboard URL

![cloudformation output](./docs/images/deploy_output.png)   


5. Change QuickSight permissions
 - Go to [quicksight admin](https://us-east-1.quicksight.aws.amazon.com/sn/admin#aws) 
 - In `QuickSight access to AWS services`, click 'Manage' button, select the S3 bucket create in step 4
![quicksight permissions](./docs/images/quicksight_perm.png) 
 - Save the change 


6. Run benchmark through Stepfunctons
 -  open StepFunctons link in step 4
 -  click the 'Start execution' button, keep the input as default, click 'Start execution'
 -  wait Stepfunctons to complete

7. View benchmark dashbaord
 - open the QuickSight dashboard link in step 4

8. Notebook experiment 
 - open the Notebook link in step 4




