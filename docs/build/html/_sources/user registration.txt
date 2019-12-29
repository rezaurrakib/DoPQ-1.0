.. _my-reference-label:

User Registration
=================
For a new user entry, just run the *user_registration.py* file. The password of the user will be encrypted and saved in the dopq database along with other information provided. Define your db path before running the script. 

.. code-block:: python

    def check_user_info(self):
        username = self.username_field.text()
        re_pass = self.retype_pass_field.text()
        email = self.email_field.text()

        # Load the Database from the address
        db_location = "your_db_path/dopq_database.db" # If No DB exist, it will create one
        db = pickledb.load(db_location, True)

.. note:: `pickleDB <https://pypi.org/project/pickleDB/>`_ is used for building the database and python hashlib framework is used for encryption. Before running the script, please make sure that you have these libraries installed in your system. 

The registration window looks like following:

.. figure:: ../resources/dopq_user_reg.png
	:align: center
	:figclass: align-center

	Figure: DoPQ User Registration Interface
