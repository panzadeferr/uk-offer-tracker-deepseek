with open('app.html', 'rb') as f:
    raw = f.read()
print('First 2 bytes:', raw[:2].hex())
if raw[:2] in [b'\xff\xfe', b'\xfe\xff']:
    content = raw.decode('utf-16')
    print('Converting from UTF-16 to UTF-8')
else:
    content = raw.decode('utf-8')
    print('Already UTF-8')
if 'charset=UTF-8' not in content:
    content = content.replace(
        '<head>',
        '<head>\n  <meta charset="UTF-8">'
    )
    print('Added charset meta tag')
with open('app.html', 'w', 
          encoding='utf-8', newline='') as f:
    f.write(content)
print('Done')