# Android Specific Code
import os
import sys
import time
import re
from os import path

import M2Crypto
from jnius import autoclass
from M2Crypto import EVP, RSA
from platform_service import SystemService
# plyer in pip is old and has bugs, so need to download source code
# manually from plyer repo to replace all the plyer source code folder
# downloaded by buildozer
from plyer.platforms.android import SDK_INT, activity

mActivity = autoclass('org.kivy.android.PythonActivity').mActivity

def getSystemLang():
    l=mActivity.getResources().getConfiguration().locale.toString()
    print "LOCALE: %s" % l
    match = re.search("^([a-z]{2})_[A-Z]+.*", l)
    if match:
        return match.group(1)
    else:
        return "en"

def getDir(append=""):
    if len(append):
        return path.join(mActivity.getExternalFilesDir(None).getPath(), append)
    else:
        return mActivity.getExternalFilesDir(None).getPath()


def realpath():
    return os.path.dirname(os.path.realpath(__file__))

# Generate a SSL certificate using module M2Crypto,  an existing one will
# be overwritten .


def generate_self_signed_cert_m2(cert_dir):
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
    cert_path = os.path.join(cert_dir, 'cert-rsa.pem')
    key_path = os.path.join(cert_dir, 'key-rsa.pem')

    if os.path.exists(cert_path):
        os.remove(cert_path)
    if os.path.exists(key_path):
        os.remove(key_path)

    # create a key pair
    key = RSA.gen_key(2048, 65537)
    key.save_key(key_path, None)
    pkey = EVP.PKey()  # Converting the RSA key into a PKey() which is stored in a certificate
    pkey.assign_rsa(key)

    # create a self-signed cert, the config is copied from src/lib/opensslVerify/openssl.cnf. not sure whether making it random is good or not.
    # time for certificate to stay valid
    cur_time = M2Crypto.ASN1.ASN1_UTCTIME()
    cur_time.set_time(int(time.time()) - 60 * 60 * 24)
    expire_time = M2Crypto.ASN1.ASN1_UTCTIME()
    expire_time.set_time(int(time.time()) + 60 * 60 * 24 * 365)
    # creating a certificate
    cert = M2Crypto.X509.X509()
    cert.set_pubkey(pkey)
    cs_name = M2Crypto.X509.X509_Name()
    cs_name.C = "US"
    cs_name.ST = 'NY'
    cs_name.L = 'New York'
    cs_name.O = 'Example, LLC'
    cs_name.CN = 'Example Company'
#    cs_name.Email = "example@example.com"
    cert.set_subject(cs_name)
    cert.set_issuer_name(cs_name)
    cert.set_not_before(cur_time)
    cert.set_not_after(expire_time)
    # self signing a certificate
    cert.sign(pkey, md="sha256")
    cert.save_pem(cert_path)
    return cert_path, key_path


class Service(SystemService):

    def zeroDir(self):
        return os.path.join(os.environ['ANDROID_APP_PATH'],  'zero')

    def getPath(self, append=""):
        return getDir(append)

    def runService(self):
        service_fullname = activity.getPackageName() + '.ServiceZn'
        service = autoclass(service_fullname)
        argument = ""
        # Generate a SSL certificate to 'data' folder,  existing pem files will
        # be overwritten . TODO: read the `data_dir` in zeronet.conf
        generate_self_signed_cert_m2(
            os.path.join(self.getPath("zero"),  'data'))
        # Start service ( system will run service.py)
        service.start(mActivity, argument)
        self.service = service
        self.running = True