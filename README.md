# aws-gcr-solutions-init-ts-repo

## How to use?

```shell
$ cd source
$ npm i
$ vim .env  # edit your .env
$ source .env
$ cd deployment
$ ./build-s3-dist.sh $DIST_OUTPUT_BUCKET $SOLUTION_NAME $VERSION
```

## How to cdk synth/diff/deploy?

```shell
$ npm run synth
$ npm run diff
$ npm run deploy
$ npm run deploy -- --parameters Param1=Value1 --parameters Param2=Value2
```

## How to format your code?

```shell
$ npm run eslint
```

## How to release?

```shell
$ # https://github.com/conventional-changelog/standard-version#release-as-a-target-type-imperatively-npm-version-like
$ npm run bump -- --release-as minor # major, minor or patch
$ # or
$ npm run bump -- --release-as 1.1.0
$ # dryrun
$ npm run bump -- --dry-run --release-as 1.1.0
$ # push tag to remote
$ git push origin v1.1.0
```
