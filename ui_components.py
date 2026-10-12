Traceback (most recent call last):
  File "<string>", line 1, in <module>
    from pathlib import Path; print(Path('work/mvp/ui_components.py').read_text(encoding='utf-8'))
                              ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yassine.kouritta\AppData\Local\Programs\Python\Python314\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\u2b50' in position 48631: character maps to <undefined>