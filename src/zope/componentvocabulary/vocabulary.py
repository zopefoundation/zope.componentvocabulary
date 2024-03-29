##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Utility Vocabulary.

This vocabulary provides terms for all utilities providing a given interface.
"""
__docformat__ = "reStructuredText"
import base64

import zope.component
from zope.component.interface import interfaceToName
from zope.interface import Interface
from zope.interface import implementer
from zope.interface import providedBy
from zope.interface import provider
from zope.interface.interfaces import IInterface
from zope.interface.interfaces import IUtilityRegistration
from zope.schema.interfaces import ITitledTokenizedTerm
from zope.schema.interfaces import ITokenizedTerm
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.interfaces import IVocabularyTokenized
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.security.proxy import removeSecurityProxy

from zope.componentvocabulary.i18n import ZopeMessageFactory as _


@implementer(ITokenizedTerm)
class UtilityTerm:
    """A term representing a utility.

    The token of the term is the name of the utility. Here is a brief example
    on how the IVocabulary interface is handled in this term as a
    utility:

    >>> from zope.interface.verify import verifyObject
    >>> from zope.schema.interfaces import IVocabulary
    >>> term = UtilityTerm(IVocabulary, 'zope.schema.interfaces.IVocabulary')
    >>> verifyObject(ITokenizedTerm, term)
    True

    >>> term.value
    <InterfaceClass zope.schema.interfaces.IVocabulary>
    >>> term.token
    'zope.schema.interfaces.IVocabulary'

    >>> term
    <UtilityTerm zope.schema.interfaces.IVocabulary, instance of InterfaceClass>
    """  # noqa: E501 line too long

    def __init__(self, value, token):
        """Create a term for value and token."""
        self.value = value
        self.token = token

    def __repr__(self):
        return '<UtilityTerm {}, instance of {}>'.format(
            self.token, self.value.__class__.__name__)


@implementer(IVocabularyTokenized)
@provider(IVocabularyFactory)
class UtilityVocabulary:
    """Vocabulary that provides utilities of a specified interface.

    Here is a short example of how the vocabulary should work.

    First we need to create a utility interface and some utilities:

    >>> class IObject(Interface):
    ...     'Simple interface to mark object utilities.'
    >>>
    >>> @implementer(IObject)
    ... class Object(object):
    ...     def __init__(self, name):
    ...         self.name = name
    ...     def __repr__(self):
    ...         return '<Object %s>' %self.name

    Now we register some utilities for IObject

    >>> from zope import component
    >>> object1 = Object('object1')
    >>> component.provideUtility(object1, IObject, 'object1')
    >>> object2 = Object('object2')
    >>> component.provideUtility(object2, IObject, 'object2')
    >>> object3 = Object('object3')
    >>> component.provideUtility(object3, IObject, 'object3')
    >>> object4 = Object('object4')

    We are now ready to create a vocabulary that we can use; in our case
    everything is global, so the context is None.

    >>> vocab = UtilityVocabulary(None, interface=IObject)
    >>> import pprint
    >>> pprint.pprint(sorted(vocab._terms.items()))
    [('object1', <UtilityTerm object1, instance of Object>),
     ('object2', <UtilityTerm object2, instance of Object>),
     ('object3', <UtilityTerm object3, instance of Object>)]

    Now let's see how the other methods behave in this context. First we can
    just use the 'in' opreator to test whether a value is available.

    >>> object1 in vocab
    True
    >>> object4 in vocab
    False

    We can also create a lazy iterator. Note that the utility terms might
    appear in a different order than the utilities were registered.

    >>> iterator = iter(vocab)
    >>> terms = list(iterator)
    >>> names = [term.token for term in terms]
    >>> names.sort()
    >>> names
    ['object1', 'object2', 'object3']

    Determining the amount of utilities available via the vocabulary is also
    possible.

    >>> len(vocab)
    3

    Next we are looking at some of the more vocabulary-characteristic API
    methods.

    One can get a term for a given value using ``getTerm()``:

    >>> vocab.getTerm(object1)
    <UtilityTerm object1, instance of Object>
    >>> vocab.getTerm(object4)
    Traceback (most recent call last):
    ...
    LookupError: <Object object4>

    On the other hand, if you want to get a term by the token, then you do
    that with:

    >>> vocab.getTermByToken('object1')
    <UtilityTerm object1, instance of Object>
    >>> vocab.getTermByToken('object4')
    Traceback (most recent call last):
    ...
    LookupError: object4

    That's it. It is all pretty straight forward, but it allows us to easily
    create a vocabulary for any utility. In fact, to make it easy to register
    such a vocabulary via ZCML, the `interface` argument to the constructor
    can be a string that is resolved via the utility registry. The ZCML looks
    like this:

    <zope:vocabulary
        name='IObjects'
        factory='zope.app.utility.vocabulary.UtilityVocabulary'
        interface='zope.app.utility.vocabulary.IObject' />

    >>> component.provideUtility(IObject, IInterface,
    ...                      'zope.app.utility.vocabulary.IObject')
    >>> vocab = UtilityVocabulary(
    ...     None, interface='zope.app.utility.vocabulary.IObject')
    >>> pprint.pprint(sorted(vocab._terms.items()))
    [('object1', <UtilityTerm object1, instance of Object>),
     ('object2', <UtilityTerm object2, instance of Object>),
     ('object3', <UtilityTerm object3, instance of Object>)]

    Sometimes it is desirable to only select the name of a utility. For
    this purpose a `nameOnly` argument was added to the constructor, in which
    case the UtilityTerm's value is not the utility itself but the name of the
    utility.

    >>> vocab = UtilityVocabulary(None, interface=IObject, nameOnly=True)
    >>> pprint.pprint([term.value for term in vocab])
    ['object1', 'object2', 'object3']
    """

    # override these in subclasses
    interface = Interface
    nameOnly = False

    def __init__(self, context, **kw):
        if kw:
            # BBB 2006/02/24, to be removed after 12 months
            # the 'interface' and 'nameOnly' parameters are supposed to be
            # set as class-level attributes in custom subclasses now.
            self.nameOnly = bool(kw.get('nameOnly', False))
            interface = kw.get('interface', Interface)
            if isinstance(interface, str):
                interface = zope.component.getUtility(IInterface, interface)
            self.interface = interface

        utils = zope.component.getUtilitiesFor(self.interface, context)
        self._terms = {
            name: UtilityTerm(self.nameOnly and name or util, name)
            for name, util in utils}

    def __contains__(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        return value in (term.value for term in self._terms.values())

    def getTerm(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        try:
            return [term for name, term in self._terms.items()
                    if term.value == value][0]
        except IndexError:
            raise LookupError(value)

    def getTermByToken(self, token):
        """See zope.schema.interfaces.IVocabularyTokenized"""
        try:
            return self._terms[token]
        except KeyError:
            raise LookupError(token)

    def __iter__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        # Sort the terms by the token (utility name)
        values = sorted(self._terms.values(), key=lambda x: x.token)
        return iter(values)

    def __len__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        return len(self._terms)


@provider(IVocabularyFactory)
class InterfacesVocabulary(UtilityVocabulary):
    interface = IInterface


@provider(IVocabularyFactory)
class ObjectInterfacesVocabulary(SimpleVocabulary):
    """A vocabulary that provides a list of all interfaces that its context
    provides.

    Here a quick demonstration:

    >>> from zope.interface import Interface, implementer
    >>> class I1(Interface):
    ...     pass
    >>> class I2(Interface):
    ...     pass
    >>> class I3(I2):
    ...     pass

    >>> @implementer(I3, I1)
    ... class Object(object):
    ...     pass

    >>> vocab = ObjectInterfacesVocabulary(Object())
    >>> import pprint
    >>> names = [term.token for term in vocab]
    >>> names.sort()
    >>> pprint.pprint(names)
    ['zope.componentvocabulary.vocabulary.I1',
     'zope.componentvocabulary.vocabulary.I2',
     'zope.componentvocabulary.vocabulary.I3',
     'zope.interface.Interface']
    """

    def __init__(self, context):
        # Remove the security proxy so the values from the vocabulary
        # are the actual interfaces and not proxies.
        component = removeSecurityProxy(context)
        interfaces = providedBy(component).flattened()
        terms = [SimpleTerm(interface, interfaceToName(context, interface))
                 for interface in interfaces]
        super().__init__(terms)


@provider(IVocabularyFactory)
class UtilityComponentInterfacesVocabulary(ObjectInterfacesVocabulary):

    def __init__(self, context):
        if IUtilityRegistration.providedBy(context):
            context = context.component
        super().__init__(
            context)


@implementer(ITitledTokenizedTerm)
class UtilityNameTerm:
    r"""Simple term that provides a utility name as a value.

    >>> t1 = UtilityNameTerm('abc')
    >>> t2 = UtilityNameTerm('\xC0\xDF\xC7')
    >>> t1.value
    'abc'
    >>> t2.value
    '\xc0\xdf\xc7'
    >>> t1.title
    'abc'
    >>> t2.title == '\xC0\xDF\xC7'
    True
    >>> ITitledTokenizedTerm.providedBy(t1)
    True

    The tokens used for form values are Base-64 encodings of the
    names, with the letter 't' prepended to ensure the unnamed utility
    is supported:

    >>> t1.token
    'tYWJj'
    >>> t2.token
    'tw4DDn8OH'

    The unnamed utility is given an artificial title for use in user
    interfaces:

    >>> t3 = UtilityNameTerm('')
    >>> t3.title
    '(unnamed utility)'

    """

    def __init__(self, value):
        self.value = value.decode() if isinstance(value, bytes) else value

    @property
    def token(self):
        # Return our value as a token.  This is required to be 7-bit
        # printable ascii. We'll use base64 generated from the UTF-8
        # representation.  (The default encoding rules should not be
        # allowed to apply.)
        return "t" + base64.b64encode(self.value.encode('utf-8')).decode()

    @property
    def title(self):
        return self.value or _("(unnamed utility)")


@implementer(IVocabularyTokenized)
class UtilityNames:
    """Vocabulary with utility names for a single interface as values.

    >>> class IMyUtility(Interface):
    ...     pass

    >>> @implementer(IMyUtility)
    ... class MyUtility(object):
    ...     pass

    >>> vocab = UtilityNames(IMyUtility)

    >>> from zope.schema.interfaces import IVocabulary
    >>> IVocabulary.providedBy(vocab)
    True
    >>> IVocabularyTokenized.providedBy(vocab)
    True

    >>> from zope.component.testing import PlacelessSetup
    >>> from zope import component
    >>> ps = PlacelessSetup()
    >>> ps.setUp()

    >>> component.provideUtility(MyUtility(), IMyUtility, 'one')
    >>> component.provideUtility(MyUtility(), IMyUtility, 'two')

    >>> unames = UtilityNames(IMyUtility)
    >>> len(list(unames))
    2
    >>> L = [t.value for t in unames]
    >>> L.sort()
    >>> L
    ['one', 'two']

    >>> 'one' in vocab
    True
    >>> 'three' in vocab
    False
    >>> component.provideUtility(MyUtility(), IMyUtility, 'three')
    >>> 'three' in vocab
    True

    If the term is not found, a ValueError is raised from ``getTerm``

    >>> 'four' in vocab
    False
    >>> vocab.getTerm('four')
    Traceback (most recent call last):
    ...
    ValueError: four

    >>> component.provideUtility(MyUtility(), IMyUtility)
    >>> '' in vocab
    True
    >>> term1 = vocab.getTerm('')
    >>> term2 = vocab.getTermByToken(term1.token)
    >>> term2.value
    ''
    >>> term3 = vocab.getTerm('one')
    >>> term3.token
    'tb25l'
    >>> term3a = vocab.getTermByToken('tb25l')
    >>> term3.value
    'one'

    If we ask ``getTermByToken`` to find a missing token, a
    ``LookupError`` is raised:

    >>> vocab.getTermByToken('no such term')
    Traceback (most recent call last):
    ...
    LookupError: no matching token: 'no such term'

    >>> ps.tearDown()
    """

    def __init__(self, interface):
        self.interface = interface

    def __contains__(self, value):
        return zope.component.queryUtility(self.interface, value) is not None

    def getTerm(self, value):
        if value in self:
            return UtilityNameTerm(value)
        raise ValueError(value)

    def getTermByToken(self, token):
        for name, ut in zope.component.getUtilitiesFor(self.interface):
            name = name.decode() if isinstance(name, bytes) else name
            if token == "t":
                if not name:
                    break
            elif UtilityNameTerm(name).token == token:
                break
        else:
            raise LookupError("no matching token: %r" % token)
        return self.getTerm(name)

    def __iter__(self):
        for name, ut in zope.component.getUtilitiesFor(self.interface):
            yield UtilityNameTerm(name)

    def __len__(self):
        """Return the number of valid terms, or sys.maxint."""
        return len(list(zope.component.getUtilitiesFor(self.interface)))
