Installation
------------
Python3 is needed, other than that, the rduty package is installation is very simple, but there are
some  dependencies which you might have to install as well:

.. code-block:: console

  $ sudo pip install paramiko
  
.. code-block:: console

   $ make install

By default rduty will be installed with the '/usr/local' prefix. You can 
change this by passing 'PREFIX=the_prefix' to make:

.. code-block:: console

   $ make PREFIX=/usr install

When rduty is executed it will check for the needed dependencies and report
if anything is missing.



