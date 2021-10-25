# cdk-bootstrapless-synthesizer

[![npm version](https://img.shields.io/npm/v/cdk-bootstrapless-synthesizer)](https://www.npmjs.com/package/cdk-bootstrapless-synthesizer)
[![downloads](https://img.shields.io/npm/dw/cdk-bootstrapless-synthesizer)](https://www.npmjs.com/package/cdk-bootstrapless-synthesizer)

A bootstrapless stack synthesizer that is designated to generate templates that can be directly used by AWS CloudFormation

## Usage

```ts
import { BootstraplessStackSynthesizer } from 'cdk-bootstrapless-synthesizer';

// ...
const app = new cdk.App();

// You can set arguments directly 
new MyWidgetServiceStack(app, 'MyWidgetServiceStack', {
  synthesizer: new BootstraplessStackSynthesizer({
    templateBucketName: 'cfn-template-bucket',
    imageAssetRepositoryName: 'ecr-repo-name',

    fileAssetBucketName: 'file-asset-bucket-${AWS::Region}',
    fileAssetRegionSet: ['us-east-1'],
    fileAssetPrefix: 'file-asset-prefix/latest/',

    imageAssetTag: 'docker-image-tag',
    imageAssetRegion: 'us-east-1',
    imageAssetAccountId: '1234567890',
  })
});

// Or by environment variables
// export BSS_TEMPLATE_BUCKET_NAME="cfn-template-bucket"
// export BSS_IMAGE_ASSET_REPOSITORY_NAME="ecr-repo-name"
// export BSS_FILE_ASSET_BUCKET_NAME="file-asset-bucket-\${AWS::Region}"
// export BSS_FILE_ASSET_REGION_SET="us-east-1,us-west-1"
// export BSS_FILE_ASSET_PREFIX="file-asset-prefix/latest/"
// export BSS_IMAGE_ASSET_TAG="docker-image-tag"
// export BSS_IMAGE_ASSET_REGION="us-east-1"
// export BSS_IMAGE_ASSET_ACCOUNT_ID="1234567890"
new MyWidgetServiceStack(app, 'MyWidgetServiceStack', {
  synthesizer: new BootstraplessStackSynthesizer()
});
```

Synth AWS CloudFormation templates, assets and upload them

```shell
$ cdk synth
$ npx cdk-assets publish -p cdk.out/MyWidgetServiceStack.assets.json -v
```

In your template

```json
{
  // ...
  "MyLayer38944FA5": {
    "Type": "AWS::Lambda::LayerVersion",
    "Properties": {
      "Content": {
        "S3Bucket": {
          "Fn::Sub": "file-asset-bucket-${AWS::Region}"
        },
        "S3Key": "file-asset-prefix/latest/8104f93f351dd2d4e69b0ab2ebe9ccff2309a573660bd75ca920ffd1808522e0.zip"
      }
    }
  }
  // ...
}
```

## Sample Project

See [Sample Project](./sample/README.md)

## API Reference

See [API Reference](./API.md) for API details.
