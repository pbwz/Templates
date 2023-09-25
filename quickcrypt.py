'''
A class for quickly encrypting and decrypting 
strings using AES-128 encryption.

Author: Paul Belland
'''

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

# failure messages
FAIL_MSG = 'Wrong password OR encrypted bytes were tampered with.'
PASS_TYPE_MSG = 'QuickCrypt only accepts strings for passwords'

class QuickCrypt:
    '''Class for encrypting strings'''
    
    def __init__(self, password:str) -> None:
        # check if type is good
        if not self._verify_password(password):
            raise ValueError(PASS_TYPE_MSG)
        
        self._password = password   # given by user
        
    def encrypt(self, data:str) -> bytes:
        '''Encrypts a given string using AES-128
        
        Input: str
        Return: encrypted bytes'''
        byte_str = b''
        
        salt = self._get_salt()
        key = self._get_key(salt)
        
        # write all to string
        cipher, enc_data = self._encrypt_data(data, key)
        byte_str += salt
        byte_str += cipher.nonce
        byte_str += enc_data
        byte_str += cipher.digest()
        
        return byte_str
    
    def decrypt(self, encrypted_str:bytes) -> str:
        '''Attempts to decrypt file'''
        # get parts of str
        salt = encrypted_str[0:32]
        nonce = encrypted_str[32:48]
        enc_data = encrypted_str[48:-16]
        tag = encrypted_str[-16:]
        
        # decrypt
        key = self._get_key(salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce = nonce)
        decrypt_data = cipher.decrypt(enc_data)
        
        try:
            cipher.verify(tag)
            return str(decrypt_data, 'utf-8')
        except ValueError:
            return FAIL_MSG
    
    def change_password(self, password:str) -> None:
        '''Allows user to change their default encryption and
        decryption password rather than making a new instance'''
        if self._verify_password(password):
            self._password = password
        
    def _verify_password(self, password:str) -> bool:
        '''Checks to make sure password is right type, returns
        True if type is str.
        
        Input: str - password
        Return: bool - password is str?'''
        if type(password) == str:
            return True
        return False
    
    def _get_key(self, salt: bytes) -> bytes:
        '''Uses the salt and password to recreate the needed key
        
        Input: bytes - salt
        Return: bytes - key'''
        key = PBKDF2(self._password, salt, dkLen=32)
        return key
    
    def _encrypt_data(self, data: str, key: bytes) -> bytes:
        '''Encrypts using AES and returns tools used
        
        Input: str - data, bytes - key
        Return: bytes - encrypted data'''
        cipher =  AES.new(key, AES.MODE_GCM)
        byte_data = bytes(data, 'utf-8')
        ciphered_data = cipher.encrypt(byte_data)
        
        return cipher, ciphered_data
    
    def _get_salt(self) -> bytes:
        '''Generates a new random salt for encryption
        
        Input: None
        Return: bytes'''
        return get_random_bytes(32)
        
def main():
    '''Main function for testing'''
    crypt = QuickCrypt('Password123')
    
if __name__ == '__main__':
    main()
