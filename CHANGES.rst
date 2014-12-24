=======
CHANGES
=======

2.0.0 (unreleased)
------------------

- Add support for Python 3.4.

- Add support for testing on Travis.


2.0.0a1 (2013-02-25)
--------------------

- Add support for Python 3.3.

- Replace deprecated ``zope.interface.classProvides`` usage with equivalent
  ``zope.interface.provider`` decorator.

- Replace deprecated ``zope.interface.implements`` usage with equivalent
  ``zope.interface.implementer`` decorator.

- Drop support for Python 2.4 and 2.5.

- When loading this package's ZCML configuration, make sure to configure
  ``zope.component`` first since we require part of its configuration.


1.0.1 (2010-09-25)
------------------

- Add not declared but needed dependency on ``zope.component``.

- Add test extra to declare test dependency on ``zope.component [test]``.


1.0 (2009-05-19)
----------------

* Initial public release, derived from zope.app.component and
  zope.app.interface to replace them.