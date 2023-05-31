# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2023-06-25

### Fix

- Restructure the architecture, decouple the user notebook code and the underlying system code
- Simplify the architecture design and eliminate the batch and quickSight functions
- Add the SNS mail subscription function to ensure that the job running results reach the user in time
- Remove VPC to reduce user cost
- Add new scenarios support

## [1.0.2] - 2023-04-19

### Fix

- [source]: reslove the issue caused by S3 policy change

## [1.0.1] - 2022-07-01

### Fix

- [notebook]: pin the source code in experimental notebook

## [1.0.0] - 2022-05-20

### Added

- All files, initial version
