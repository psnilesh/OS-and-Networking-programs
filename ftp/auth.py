import crypt
import pwd
import spwd


"""
    Checks whether the given username and password
    combo exists in the system.
    @return User ID of the user on success, None on failure.
"""


def authenticate(username='', passwd=''):
    # Fetch user id from passwd file first
    try:
        st_user = pwd.getpwnam(username)
        # Extract password from /etc/shadow file
        encrypted_passwd = spwd.getspnam(username).sp_pwdp
        # Digest the given password and compare the hash values
        passwd = crypt.crypt(
            passwd,
            encrypted_passwd[:encrypted_passwd.index('$', 3) + 1])
        if passwd != encrypted_passwd:
            return None
        return st_user.pw_uid
    except KeyError as ke:
        print(ke)
        return None
