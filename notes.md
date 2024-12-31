continue with the document summarization


Build a the docker image that does the summarizattion 


Need to work on the ochestration and deploy the LLM


### Deployment step.

Have the script that will download the model.

Compile LLMA CPP locally.

Clone the project and create 

Have a script that will convert the model to 


https://medium.com/@ramanbazhanau/preparing-fastapi-for-production-a-comprehensive-guide-d167e693aa2b


## Manged to run 


 --create password using

 sudo sh -c "echo -n 'espy:' >>  docker/nginx/.htpasswd"
sudo sh -c "openssl passwd -apr1 >>  docker/nginx/.htpasswd"



Managed to deploy the model, need now to work on the summarization ochestration


### NEed to sort out the issue with news not updating correctly



CPU information

AMD EPYC 7282 16-Core Processor
2.7 GHz
Cache 512kb


How to run flyte on the UI
https://github.com/davidmirror-ops/flyte-the-hard-way/blob/main/docs/on-premises/single-node/003-ingress-tls.md


### Notes

As I have written the workflow, now the next step should be checking making it work and finish the ochestration

kubectl logs abvkww49dppvwqvrkp5s-n0-0  -n flytesnacks-development

https://gist.github.com/ruanbekker/bb62d7e2a77493497a2acbc3d0a649d3


kubectl create secret -n <project>-<domain> generic user-info --from-literal=user_secret=mysecret
kubectl create secret -n <project>-<domain>  generic credentials --from-env-file=.test-secret


` kubectl create secret -n flytesnacks-development generic database-credentials --from-env-file=.env_db`


database_secret_request = [
    Secret(key="USER", group="postgres",
           mount_requirement=Secret.MountType.ENV_VAR,),
    Secret(key="PASSWORD", group="postgres",
           mount_requirement=Secret.MountType.ENV_VAR,),
    Secret(key="HOST", group="postgres",
           mount_requirement=Secret.MountType.ENV_VAR,),
    Secret(key="PORT", group="postgres",
           mount_requirement=Secret.MountType.ENV_VAR,),
    Secret(key="DB", group="postgres",
           mount_requirement=Secret.MountType.ENV_VAR,),
]
