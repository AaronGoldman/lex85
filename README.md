# lex85

A base85 encoding with stable
lexicographic sorting to the raw bytes

## lexicographic base85 alphabet
```
#$%&()*+-0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_abcdefghijklmnopqrstuvwxyz{|}
```
---
We want to put bytes into ascii strings with more density then b64.

4/3 blowup for b64 but only 5/4 blowup for lex85.

Our target environment for lex85 is CSV, TSV, JSON, and programming language literal strings.
If we look at how many bytes a char if encoded in json is their are
93 chars that are encoded as a single byte.
```python
In [0]: import json
In [1]: {i:chr(i) for i in range(256) if len(json.dumps(chr(i)))<=3}  # "c"
Out[1]:
 32: ' ',  33: '!',  35: '#',  36: '$',  37: '%',  38: '&',  39: "'",  40: '(',
 41: ')',  42: '*',  43: '+',  44: ',',  45: '-',  46: '.',  47: '/',  48: '0',
 49: '1',  50: '2',  51: '3',  52: '4',  53: '5',  54: '6',  55: '7',  56: '8',
 57: '9',  58: ':',  59: ';',  60: '<',  61: '=',  62: '>',  63: '?',  64: '@',
 65: 'A',  66: 'B',  67: 'C',  68: 'D',  69: 'E',  70: 'F',  71: 'G',  72: 'H',
 73: 'I',  74: 'J',  75: 'K',  76: 'L',  77: 'M',  78: 'N',  79: 'O',  80: 'P',
 81: 'Q',  82: 'R',  83: 'S',  84: 'T',  85: 'U',  86: 'V',  87: 'W',  88: 'X',
 89: 'Y',  90: 'Z',  91: '[',  93: ']',  94: '^',  95: '_',  96: '`',  97: 'a',
 98: 'b',  99: 'c', 100: 'd', 101: 'e', 102: 'f', 103: 'g', 104: 'h', 105: 'i',
106: 'j', 107: 'k', 108: 'l', 109: 'm', 110: 'n', 111: 'o', 112: 'p', 113: 'q',
114: 'r', 115: 's', 116: 't', 117: 'u', 118: 'v', 119: 'w', 120: 'x', 121: 'y',
122: 'z', 123: '{', 124: '|', 125: '}', 126: '~'
```
we need to pick 85 chars for our alphabet

* we drop `32: ' '` since it is ambiguous with tab
* we drop `33: '!'` to reserve it as less then all lex85 chars
* we drop `34: '"'` since it is the json string container
* we drop `39: "'"` since it is a string container
* we drop `44: ','` since it is a delimiter
* we drop `46: '.'` since it is a delimiter
* we drop `47: '/'` since it is a delimiter
* we drop `92: '\'` since it is the json string escaping
* we drop ```96: '`'``` since it is a string container
* we drop `126: '~'` to reserve it as grater then all lex85 chars

giving us the alphabet
    `"#$%&()*+-0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_abcdefghijklmnopqrstuvwxyz{|}"`

> Note:
> * Sort Order
>
>   The alphabet is in lexicographic sort order this is important since it allows for the encoded strings and decoded bytes to sort in the same order.
>
> * Fencepost
>
>   '!' and '~' are not in the lex85 alphabet but are in printable ascii so fencepost can be constructed
>
>   `"aa!"` will sort before `"aa#"`
>
>   `"aa~"` will sort after not only "aa}" but `"aa}}}}}}}}}}}}...`
>
>   Fenceposts allow programmers get exclusive ranges using only inclusive range queries.

## encoding

```
 -------------------------------- 
| C1    | C2   | C3  | C4  | C5  |
|--------------------------------|
| i unsigned 32 bit integer      |
|--------------------------------|
| byte1 | byte2 | byte3 | byte4  |
 --------------------------------

i = (C1 * 85 ** 4) + (C2 * 85 ** 3) + (C3 * 85 ** 2) + (C4 * 85)+ C5
i = (b1 << 24) + (b2 << 16) + (b3 << 8) + (b4 << 0)
```

If the number of chars is not modulo 5 then pad with `b85(84)`

If the number of bytes is not modulo 4 then pad with `0x00`

Then drop the length of the pad from the output

```python
base85_alphabet = "#$%&()*+-0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_abcdefghijklmnopqrstuvwxyz{|}" 
integer2character85 = base85_alphabet
character2integer85 = {character: index for index, character in enumerate(base85_alphabet)}

def encode85(buffer):
    pad = (-(len(buffer) % -4))  # bytes to get to multiple of 4
    buffer = buffer + b'\x00'*pad
    encoded = [''] * ((len(buffer)//4)*5)
    for i in range(0, len(buffer)//4):
        integer = ((buffer[4 * i + 0] << 24)|
                   (buffer[4 * i + 1] << 16)|
                   (buffer[4 * i + 2] << 8 )|
                   (buffer[4 * i + 3] << 0 ))
        encoded[5 * i + 0] = integer2character85[integer // (85**4) % 85]
        encoded[5 * i + 1] = integer2character85[integer // (85**3) % 85]
        encoded[5 * i + 2] = integer2character85[integer // (85**2) % 85]
        encoded[5 * i + 3] = integer2character85[integer // (85**1) % 85]
        encoded[5 * i + 4] = integer2character85[integer // (85**0) % 85]
        if integer >> 32:
            return OverflowError(f"{integer} > uint32_max")
    return ''.join(encoded)[:len(encoded)-pad]

def decode85(string):
    pad = (-(len(string) % -5))  # characters to get to multiple of 5
    string = string + '}'*pad
    buffer = bytearray(len(string) // 5 * 4)
    for i in range(0, len(string) // 5):
        integer = (character2integer85[string[i * 5 + 0]] * (85 ** 4) +  
                   character2integer85[string[i * 5 + 1]] * (85 ** 3) +
                   character2integer85[string[i * 5 + 2]] * (85 ** 2) +
                   character2integer85[string[i * 5 + 3]] * (85 ** 1) +
                   character2integer85[string[i * 5 + 4]] * (85 ** 0))
        buffer[i * 4 + 0] = integer >> 24 & 0xff
        buffer[i * 4 + 1] = integer >> 16 & 0xff
        buffer[i * 4 + 2] = integer >>  8 & 0xff
        buffer[i * 4 + 3] = integer >>  0 & 0xff
    return bytes(buffer[:len(buffer)-pad])
```

## Recommended syntax for tagging lex85
prefix `l`
```python
# int literal stile
# lxHU}#zJb 
In [1]: 0x68656c6c6f  
Out[1]: 448378203247

# tagged string literal stile
# l"HU}#zJb" 
In [2]: b"\x68\x65\x6c\x6c\x6f"
Out[2]: b'hello'

# multibase stile
# multibase.decode("lHU}#zJb") 
In [3]: multibase.decode("f68656c6c6f")
Out[3]: b'hello'
```