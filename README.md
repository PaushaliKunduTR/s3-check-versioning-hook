# Set Up Proactive Governance Guardrails using CloudFormation Hooks

## paushalisb::guardraildemo::hook

### Goal:
- Set Up Proactive Governance Guardrails in an account

### Set Up CFN CLI
```
pip install cloudformation-cli cloudformation-cli-python-plugin
```
### Initialize Hook

```
$ cfn init
Initializing new project
Do you want to develop a new resource(r) or a module(m) or a hook(h)?.
>> h
What's the name of your hook type?
(Organization::Service::Hook)
>> paushalisb::guardraildemo::hook
Select a language for code generation:
[1] python36
[2] python37
(enter an integer): 
>> 2
Use docker for platform-independent packaging (Y/n)?
This is highly recommended unless you are experienced 
with cross-platform Python packaging.
>> Y
```

### Set Up Hook

```
(base) (.venv)$ cfn generate
Generated files for paushalisb::guardraildemo::hook
```

The <i>cfn generate</i> command generates handlers.py and models.py files within src/ directory

Implement S3 Versioning Check within handlers.py. 

### Validate

```
$ cfn validate
```
The following optional command builds and packages the hook to generate a zip file. The generated zip file can be used when deploying the hook across multiple regions/accounts.

```
$ cfn submit --dry-run
```

### Build and Register Hook
```
$ cfn submit --set-default
```

The hook can be viewed by navigating to registry/activated-extensions/hooks on the CloudFormation console

### Activate Hook

```
$ aws cloudformation describe-type --type-name paushalisb::guardraildemo::hook --type HOOK
```

```
$ aws cloudformation --region us-east-1 set-type-configuration \
  --configuration '{"CloudFormationConfiguration":{"HookConfiguration":{"TargetStacks":"ALL","Properties":{ "excludedBuckets": "excluded,baseline"},"FailureMode":"FAIL"}}}' \
  --type-arn $HOOK_TYPE_ARN
  ```

  ### Test Hook
  There are two sample CF templates within templates/ folder which provision compliant (S3 bucket with versioning enabled) and non-compliant (S3 bucket with versioning not enabled) stacks.

<i>bucket_with_versioning.yaml</i> would invoke the hook, pass validation and create a new S3 bucket.

<i>bucket-noncompliant.yaml</i> would fail validation when the hook gets invoked upon stack initiation; and the creation of an S3 bucket would fail.