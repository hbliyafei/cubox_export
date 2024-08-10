# Cubox export
将 cubox 内容导出并删除原始内容

## 使用
1. 获取 token 内容
2. 调用方法
```python
directory = '导出文件保存位置'
token = '你的 token'
# export markdown:md, text:text: pdf:pdf: html:html
cubox = Cubox(setup_logging(), token, directory, 'md', False)
cubox.start()
```