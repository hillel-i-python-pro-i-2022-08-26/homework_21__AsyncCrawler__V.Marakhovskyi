# Homework # 21. (Crawler)

---
![Main workflow](https://github.com/hillel-i-python-pro-i-2022-08-26/homework_21__AsyncCrawler__V.Marakhovskyi/actions/workflows/main-workflow.yml/badge.svg?branch=crawler)
![IDE](https://img.shields.io/badge/PyCharm-000000.svg?&style=for-the-badge&logo=PyCharm&logoColor=white)
![REPO](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)
## 👨‍💻 Homework

Async crawler with variable parameters: depth and qtty of processed URLs. 
Also available start via console. Default params: 
-processed_urls: 30
-depth: 2
All packed in Docker.

### 🎬 Run locally

Run an application locally with automatic installing of all requirements.

```shell
make homework-i-run
```

### 🎛️ Run in console with argparse
Run an application locally through console with variable arguments. 

```shell
python async_deep_crawler.py -processed_urls 40 -depth 2
```

### 📦 Run in docker

Run an application in Docker.

```shell
make d-homework-i-run
```

### 🛣️ Install pre-commit and dependencies:
```shell
make init-dev
```


### 🧽🪣 Purge

Delete all created artifacts from run.

```shell
make d-homework-i-purge
```
