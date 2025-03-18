# polymarker-webui

[//]: # (![polymarker logo]&#40;pmwui/static/images/Logo.png "polymarker logo"&#41;)

[//]: # (![jic logo]&#40;pmwui/static/images/jic.png "jic logo"&#41;)


A sample project that exists as an aid to the [Python Packaging User
Guide][packaging guide]'s [Tutorial on Packaging and Distributing
Projects][distribution tutorial].

This project does not aim to cover best practices for Python project
development as a whole. For example, it does not provide guidance or tool
recommendations for version control, documentation, or testing.

[The source for this project is available here][src].

The metadata for a Python project is defined in the `pyproject.toml` file,
an example of which is included in this project. You should edit this file
accordingly to adapt this sample project to your needs.

----

This is the README file for the project.

displayed as the project homepage on common code-hosting services, and should be
written for that purpose.

Typical contents for this file would include an overview of the project, basic
usage examples, etc. Generally, including the project changelog in here is not a
good idea, although a simple “What's New” section for the most recent version
may be appropriate.

[packaging guide]: https://packaging.python.org

[distribution tutorial]: https://packaging.python.org/tutorials/packaging-projects/

[src]: https://github.com/pypa/sampleproject

[rst]: http://docutils.sourceforge.net/rst.html

[md]: https://tools.ietf.org/html/rfc7764#section-3.5 "CommonMark variant"

[md use]: https://packaging.python.org/specifications/core-metadata/#description-content-type-optional


---

## install

---

[goz24vof@pm ~]$ sudo luseradd polymarker

---

Install polymarker as described [here](https://github.com/cb2e6f/bio-polymarker/blob/master/README.md)

---


[goz24vof@pm ~]$ sudo dnf install nginx
[goz24vof@pm ~]$ sudo firewall-cmd --permanent --add-service=http
success
[goz24vof@pm ~]$ sudo firewall-cmd --reload
success


[goz24vof@pm ~]$ sudo systemctl enable nginx.service 

[goz24vof@pm ~]$ sudo systemctl start nginx.service 






[goz24vof@pm ~]$ sudo dnf install -y mariadb mariadb-server

[goz24vof@pm ~]$ sudo systemctl enable mariadb
[goz24vof@pm ~]$ sudo systemctl start mariadb

[goz24vof@pm ~]$ sudo mariadb-secure-installation 


----


[goz24vof@pm ~]$ sudo mariadb -u root -p



3 rows in set (0.009 sec)

MariaDB [(none)]> CREATE USER polymarker;
Query OK, 0 rows affected (0.013 sec)

MariaDB [(none)]> GRANT * ON *.* TO "polymarker"@"localhost";
ERROR 1064 (42000): You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near '* ON *.* TO "polymarker"@"localhost"' at line 1
MariaDB [(none)]> GRANT * ON *.* TO 'polymarker'@'localhost';
ERROR 1064 (42000): You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near '* ON *.* TO 'polymarker'@'localhost'' at line 1
MariaDB [(none)]> GRANT ALL ON *.* TO 'polymarker'@'localhost';
ERROR 1133 (28000): Can't find any matching row in the user table
MariaDB [(none)]> GRANT ALL ON *.* TO 'polymarker';
Query OK, 0 rows affected (0.012 sec)







[goz24vof@pm ~]$ mariadb -u polymarker -p

MariaDB [(none)]> CREATE DATABASE polymarker_webui;




-------



[goz24vof@pm ~]$ sudo dnf install -y mariadb-connector-c-devel

-------


[goz24vof@pm ~]$ sudo dnf install -y python3-devel


-------


pip install --upgrade pip


----------





