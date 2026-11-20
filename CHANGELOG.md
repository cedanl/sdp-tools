# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Fix
 - Importing `minio_file` no longer silences urllib3's `InsecureRequestWarning` for the whole process (#14).
   Code that makes unverified HTTPS requests in the same process now sees this warning again.


## [ 2024.4.4 ] (2024-09-19)

### Fix
 - Example text
