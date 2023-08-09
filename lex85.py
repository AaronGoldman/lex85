base85_alphabet = "#$%&()*+-0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_abcdefghijklmnopqrstuvwxyz{|}" 
integer2character85 = base85_alphabet
character2integer85 = {character: index for index, character in enumerate(base85_alphabet)}

def encode85(buffer):
    pad = (-(len(buffer) % -4))
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
    pad = (-(len(string) % -5))
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

def test():
    for test in open("tests.txt", "r"):
        # hex b85
        expected_bytes_hex, expected_b85 = test.strip("\n").split(" ")
        expected_bytes = bytes.fromhex(expected_bytes_hex)

        calculated_b85 = encode85(expected_bytes)
        calculated_bytes = decode85(expected_b85)
        if calculated_b85 == expected_b85:
            print(".", end="")
        else:
            print(f'raw={expected_bytes_hex}, {expected_b85=}, {calculated_b85=}')
        
        if calculated_bytes == expected_bytes:
            print(".", end="")
        else:
            print(f'raw={expected_b85}, {expected_bytes=}, {calculated_bytes.hex()=}')
    print()

if __name__ == "__main__":
    test()