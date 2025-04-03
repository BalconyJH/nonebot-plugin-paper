<!-- markdownlint-disable MD033 MD036 MD041 MD045 -->
<div align="center">
  <a href="https://v2.nonebot.dev/store">
    <img src="./docs/NoneBotPlugin.svg" width="300" alt="logo">
  </a>
</div>

<div align="center">

# NoneBot-Plugin-Paper

_✨ NoneBot arXiv Paper Search Plugin ✨_

<a href="">
  <img src="https://img.shields.io/pypi/v/nonebot-plugin-paper.svg" alt="pypi" />
</a>
<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">
<a href="https://pdm.fming.dev">
  <img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fcdn.jsdelivr.net%2Fgh%2Fpdm-project%2F.github%2Fbadge.json" alt="pdm-managed">
</a>
<a href="https://github.com/nonebot/plugin-alconna">
  <img src="https://img.shields.io/badge/Alconna-resolved-2564C2" alt="alc-resolved">
</a>

<br/>

<a href="https://registry.nonebot.dev/plugin/nonebot-plugin-paper:nonebot_plugin_paper">
  <img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fnbbdg.lgc2333.top%2Fplugin%2Fnonebot-plugin-paper" alt="NoneBot Registry" />
</a>
<a href="https://registry.nonebot.dev/plugin/nonebot-plugin-paper:nonebot_plugin_paper">
  <img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fnbbdg.lgc2333.top%2Fplugin-adapters%2Fnonebot-plugin-paper" alt="Supported Adapters" />
</a>

<br />

[//]: # (<a href="#-screenshots">)

[//]: # (  <strong>📸 Demo & Preview</strong>)

[//]: # (</a>)

[//]: # (&nbsp;&nbsp;|&nbsp;&nbsp;)

[//]: # (<a href="#-installation">)

[//]: # (  <strong>📦️ Download Plugin</strong>)

[//]: # (</a>)

</div>

## 📖 Introduction

NoneBot arXiv Paper search
Plugin for [arXiv APIs](https://info.arxiv.org/help/api/tou.html)

Wiki: 👉 [Portal](https://github.com/BalconyJH/nonebot-plugin-paper/wiki)

> [!IMPORTANT]
> **Star this project** to receive all release notifications from GitHub without delay!
> ⭐️

<img width="100%" src="https://starify.komoridevs.icu/api/starify?owner=BalconyJH&repo=nonebot-plugin-paper" alt="starify" />

## 💿 Installation

Choose **one** of the following methods

> [!TIP]
> Multiple rendering methods are provided for paper information. By default, `plaintext`
> is used, which means no rendering, text-only output.
> In this case, the plugin requires no additional dependencies.
> Optional dependencies include `playwright`, `skia`, and `pillow`. Use
`nonebot-plugin-paper[skia]` during installation
> to include required dependencies.

<details open>
<summary>[Recommended] Install using nb-cli</summary>
Open command line in the Bot root directory and enter the following command

```shell
nb plugin install nonebot-plugin-paper
```

</details>
<details>
<summary>Install using package manager</summary>

```shell
pip install nonebot-plugin-paper
# or, use poetry
poetry add nonebot-plugin-paper
# or, use pdm
pdm add nonebot-plugin-paper
```

Open the configuration file in your NoneBot project root directory and append to the
`[plugin]` section

```toml
plugins = ["nonebot_plugin_paper"]
```

</details>

## ⚙️ Configuration

For ArxivConfig settings, please refer
to：👉 [ArxivConfig Configuration](https://balconyjh.github.io/aioarxiv/configuration.html)

|    Config Item     | Required |    Default    |                                      Description                                       |
|:------------------:|:--------:|:-------------:|:--------------------------------------------------------------------------------------:|
| arxiv_paper_render |    No    |   plaintext   |                                   Paper render type                                    |
|    arxiv_config    |    No    | ArxivConfig() | Can be passed via nonebot.init(), config model will automatically read dotenv settings |

## 🎉 Usage

> [!note]
> Please check your `COMMAND_START` and the above configuration items. Default prefix is
`/`

### Command Tree

```bash
paper --search | -s [keyword]
                  --sort ['relevance', 'lastUpdatedDate', 'submittedDate']
                  --order ['ascending', 'descending']
                  --start [start]
      -id [paper_id]
```

### Search by Keyword

```bash
/paper --search quantum computing
```

### Search by Paper ID

```bash
/paper -id 2409.12922
```

## 💖 Acknowledgments

- [`Polyisoprene`](https://github.com/Polyisoprene): Provided MVP implementation of skia
  rendering component
- [`HibiKier`](https://github.com/HibiKier): Implemented command tree building for the
  plugin
- [`KomoriDev/Starify`](https://github.com/BalconyJH/Starify)：Provided cool badges

### Contributors

Thanks to these developers who contributed to this project:

<a href="https://github.com/BalconyJH/nonebot-plugin-paper/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=BalconyJH/nonebot-plugin-paper&max=1000" alt="contributors" />
</a>

## 📄 License

This project is open-sourced under the [GPL-3.0 license](./LICENSE)