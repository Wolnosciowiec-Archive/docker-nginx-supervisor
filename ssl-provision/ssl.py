#!/usr/bin/env python

from glob import glob
import os
import re
import time


class NginxSSLProvision:
    __certificates_path = "/etc/letsencrypt/live/%s/privkey.pem"
    __missing_files = []
    __maintenance_nginx_running = False

    @property
    def missing_files(self):
        return self.__missing_files

    def __validate_configuration_files(self, directory):
        self.__missing_files = []
        files = glob(directory + '/*.conf')

        for file in files:
            self.__parse_configuration_file(file)

    def __parse_configuration_file(self, path):
        handle = open(path)
        contents = handle.read()
        handle.close()

        server_blocks = re.findall(r'server\ \{(.*)\}', contents, re.DOTALL)

        for block in server_blocks:
            # the regexp is sometimes joining a few server {} blocks into one, so just-in-case we can separate them
            sub_blocks = block.split('server {')

            for sub_block in sub_blocks:
                self.__parse_server_block(sub_block)

    def __parse_server_block(self, block_content):
        """
            server { }

        :param block_content:
        :return:
        """

        # do not touch non-http configuration
        if len(re.findall(r'listen.*(ssl).*\;', block_content)) == 0:
            return

        # easiest one: detect missing paths to SSL keys
        if "ssl_certificate_key" in block_content:
            self.__parse_certificate_key(re.findall(r'ssl_certificate_key (.*)\;', block_content)[0])
            return

        # match server name against SSL key file name
        if "server_name" in block_content:
            self.__parse_server_name(re.findall(r'server_name (.*)\;', block_content)[0])
            return

        raise Exception('Cannot parse server block, no any known attributes were used')

    def __parse_certificate_key(self, block_content):
        """
        ssl_certificate_key (.*);

        :param block_content:
        :return:
        """

        if not os.path.isfile(block_content) and block_content not in self.__missing_files:
            self.__missing_files.append(block_content)

    def __parse_server_name(self, block_content):
        """
           server_name (.*);

        :param block_content:
        :return:
        """

        if block_content == "_":
            return

        domains = block_content.split(' ')

        for domain in domains:
            certificate_path = self.__certificates_path.replace('%s', domain)

            if not os.path.isfile(certificate_path) and certificate_path not in self.__missing_files:
                self.__missing_files.append(certificate_path)

    def run_maintenance_nginx(self):
        """
        Run nginx in maintenance mode
        :return:
        """

        # do not run twice
        if self.__maintenance_nginx_running:
            return

        print(' >> Running maintenance nginx')
        self.kill_nginx()
        os.system("nginx -c /ssl-provision/nginx.conf &")
        self.__maintenance_nginx_running = True

    def run_target_nginx(self):
        """
        Run nginx normally
        :return:
        """

        print(' >> Running target nginx')
        self.kill_nginx()
        self.__maintenance_nginx_running = False
        os.system("nginx -g \"daemon off;\"")

    def kill_nginx(self):
        """
        Stops a nginx instance
        :return:
        """

        os.system('killall nginx || true')

    def listen(self, directory):
        """
        Listen for changes in SSL configuration
        :param directory:
        :return:
        """

        while True:
            self.__validate_configuration_files(directory)

            print('>> Missing files:')
            print(self.missing_files)

            if len(self.missing_files) > 0:
                self.run_maintenance_nginx()
            else:
                self.run_target_nginx()

            time.sleep(1)

provision = NginxSSLProvision()
provision.listen('/etc/nginx/sites-enabled')
