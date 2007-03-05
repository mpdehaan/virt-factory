#!/usr/bin/python

import pprint
import time

import test_case

from modules import user

class UserTestCase(test_case.TestCase):
    def __init__(self):
        self.cases = [self.userList,
                      self.userGet,
                      self.userAdd,
                      self.userAddNull,
                      self.userAddLongUser,
                      self.userAddEmptyUser,
                      self.userFail]
        test_case.TestCase.__init__(self)
        self.getToken()

        self.__setupData()

    def __setupData(self):
        self.user_info_null = {}
        self.user_info_long_user = self.__getUserInfo()
        self.user_info_long_user['username'] = "this is a very very very very very very very very very very very very very very very very very very very very very long username"

    def __getUserInfo(self):
        username = "test_user_name_space_%s" % time.time()
        password = "TestPasswordBlippy"
        first_name = "Test"
        last_name = "Last"
        middle_name = "T"
        description = "a angry lonely man with his heart set on breaking things"
        email = "testuser+alikins@redhat.com"
        self.user_info_works = {'username': username,
                                'password': password,
                                "first": first_name,
                                "last": last_name,
                                "middle": middle_name,
                                "description": description,
                                "email": email}
        return self.user_info_works

    def userList(self):
        self.server.user_list(self.token, {})
        self.logPass("userList", "user_list seemed to execute without errors")

    def userGet(self):

        ul = self.server.user_list(self.token, {})
        for u in ul[1]['data']:
            user_data = self.server.user_get(self.token, {'id': u['id']})
            ud = user_data[1]['data']
            if len(u.values()) != len(ud.values()):
                self.logFail("user_get", "length of hashes did not match")
                return
            
            for field in u.keys():
                if u[field] != ud[field]:
                    self.logFail("user_get", "fields mismatch")
                    return

        self.logPass("user_get", "no reason really")


    def userAddNull(self):
        self.user_info_null = {}

        ua = self.server.user_add(self.token, self.user_info_works)
        if ua[0] != 0:
            self.logFail("userAddNull", comment="Got a non zero return code", rc=ua)
            return

        self.logPass("userAddNull", comment="Seemed to work", rc=ua)

    def userAddLongUser(self):
        ua = self.server.user_add(self.token, self.user_info_long_user)
        
        if ua[0] != 0:
            self.logFail("userAddLongUser", comment="Got a non zero return code", rc=ua)
            return

        self.logPass("userAddLongUser", comment="Seemed to work", rc=ua)

    def userAddEmptyUser(self):
        info = self.__getUserInfo()
        info['username'] = ""

        ua = self.server.user_add(self.token, info)

        if ua[0] == 0:
            self.logFail("userAddEmptyUser", comment="Got a zero return code when attempting to add a null user (username=\"\") ", rc=ua)
            return

        self.logPass("userAddEmptyUser", comment="Seemed to work", rc=ua)

    def userAdd(self):
        ua = self.server.user_add(self.token, self.user_info_works)
        if ua[0] != 0:
            self.logFail("userAdd", comment="Got a non zero return code", rc=ua)
            return

        self.logPass("userAdd", comment="Seemed to work", rc=ua)
                     

    def userFail(self):
        print this_doesnt_exist_just_to_test_the_test_case
        

testcase = UserTestCase
