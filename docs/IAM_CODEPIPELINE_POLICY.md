# Política IAM para CodePipeline - blacklist-CI

## Rol

**Nombre:** `AWSCodePipelineServiceRole-us-east-1-blacklist-CI`  
**ARN:** `arn:aws:iam::938595516179:role/AWSCodePipelineServiceRole-us-east-1-blacklist-CI`  
**Política a editar:** `AWSCodePipelineServiceRole-us-east-1-blacklist-CI`

## Política completa

Reemplazar todo el contenido de la política con el siguiente JSON:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowS3BucketAccess",
            "Effect": "Allow",
            "Action": [
                "s3:GetBucketVersioning",
                "s3:GetBucketAcl",
                "s3:GetBucketLocation"
            ],
            "Resource": [
                "arn:aws:s3:::codepipeline-us-east-1-0e91f6c23ba9-4281-b91a-7be528681a82"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:ResourceAccount": "938595516179"
                }
            }
        },
        {
            "Sid": "AllowS3ObjectAccess",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:GetObjectVersion"
            ],
            "Resource": [
                "arn:aws:s3:::codepipeline-us-east-1-0e91f6c23ba9-4281-b91a-7be528681a82/*"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:ResourceAccount": "938595516179"
                }
            }
        },
        {
            "Sid": "AllowElasticBeanstalkS3",
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket",
                "s3:DeleteObject",
                "s3:GetObject",
                "s3:GetObjectAcl",
                "s3:GetObjectVersion",
                "s3:GetObjectVersionAcl",
                "s3:GetBucketVersioning",
                "s3:GetBucketAcl",
                "s3:GetBucketLocation",
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:ListBucket",
                "s3:ListBucketVersions"
            ],
            "Resource": [
                "arn:aws:s3:::elasticbeanstalk-us-east-1-938595516179",
                "arn:aws:s3:::elasticbeanstalk-us-east-1-938595516179/*"
            ]
        },
        {
            "Sid": "AllowElasticBeanstalkFull",
            "Effect": "Allow",
            "Action": [
                "elasticbeanstalk:*",
                "ec2:Describe*",
                "autoscaling:Describe*",
                "autoscaling:*",
                "elasticloadbalancing:Describe*",
                "cloudwatch:Describe*",
                "cloudwatch:List*",
                "cloudwatch:GetMetricStatistics",
                "cloudformation:GetTemplate",
                "cloudformation:Describe*",
                "cloudformation:ListStackResources",
                "cloudformation:ValidateTemplate",
                "cloudformation:EstimateTemplateCost",
                "cloudformation:UpdateStack",
                "cloudformation:CreateStack",
                "iam:PassRole"
            ],
            "Resource": "*"
        }
    ]
}
```

## Permisos por statement

| Sid | Recurso | Para qué sirve |
|-----|---------|----------------|
| `AllowS3BucketAccess` | Bucket de CodePipeline | Leer metadata del bucket de artefactos del pipeline |
| `AllowS3ObjectAccess` | Objetos del bucket de CodePipeline | Leer/escribir artefactos entre etapas del pipeline |
| `AllowElasticBeanstalkS3` | Bucket `elasticbeanstalk-us-east-1-938595516179` | Subir, leer y eliminar versiones de la app en EB |
| `AllowElasticBeanstalkFull` | `*` | Desplegar en EB, gestionar CloudFormation stacks, AutoScaling y pasar roles |

## Cómo aplicar

1. Ir a **IAM → Roles → AWSCodePipelineServiceRole-us-east-1-blacklist-CI**
2. Clic en la política `AWSCodePipelineServiceRole-us-east-1-blacklist-CI`
3. Clic en **Editar política → pestaña JSON**
4. Reemplazar todo el contenido con el JSON de arriba
5. Clic en **Siguiente → Guardar cambios**
