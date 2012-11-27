import datetime
import os
import random
import re
import string
import uuid
from decimal import Decimal


class GeneratorException(Exception):
    pass


class IGNORE_EMPTY(object):
    pass


class Generator(object):
    coerce_type = staticmethod(lambda x: x)
    empty_value = None
    empty_p = 0

    def __init__(self, empty_p=None, empty_value=IGNORE_EMPTY, coerce=None):
        if empty_p is not None:
            self.empty_p = empty_p
        if empty_value is not IGNORE_EMPTY:
            self.empty_value = empty_value
        if coerce is not None:
            self.coerce_type = coerce

    def coerce(self, value):
        return self.coerce_type(value)

    def generate(self):
        raise NotImplementedError

    def get_value(self):
        if random.random() < self.empty_p:
            return self.empty_value
        value = self.generate()
        return self.coerce(value)


class StaticGenerator(Generator):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(StaticGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        return self.value


class CallableGenerator(Generator):
    def __init__(self, value, args=None, kwargs=None, *xargs, **xkwargs):
        self.value = value
        self.args = args or ()
        self.kwargs = kwargs or {}
        super(CallableGenerator, self).__init__(*xargs, **xkwargs)

    def generate(self):
        return self.value(*self.args, **self.kwargs)


class UUIDGenerator(Generator):
    def __init__(self, max_length=None, **kwargs):
        self.max_length = max_length
        super(UUIDGenerator, self).__init__(**kwargs)

    def generate(self):
        value = unicode(uuid.uuid1())
        if self.max_length is not None:
            value = value[:self.max_length]
        return value


class StringGenerator(Generator):
    coerce_type = unicode
    singleline_chars = string.letters + u' '
    multiline_chars = singleline_chars + u'\n'

    def __init__(self, chars=None, multiline=False, min_length=1, max_length=1000, *args, **kwargs):
        assert min_length >= 0
        assert max_length >= 0
        self.min_length = min_length
        self.max_length = max_length
        if chars is None:
            if multiline:
                self.chars = self.multiline_chars
            else:
                self.chars = self.singleline_chars
        else:
            self.chars = chars
        super(StringGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        length = random.randint(self.min_length, self.max_length)
        value = u''
        for x in xrange(length):
            value += random.choice(self.chars)
        return value


class SlugGenerator(StringGenerator):
    def __init__(self, chars=None, *args, **kwargs):
        if chars is None:
            chars = string.ascii_lowercase + string.digits + '-'
        super(SlugGenerator, self).__init__(chars, multiline=False, *args, **kwargs)


class LoremGenerator(Generator):
    coerce_type = unicode
    common = True
    count = 3
    method = 'b'

    def __init__(self, count=None, method=None, common=None, max_length=None, *args, **kwargs):
        if count is not None:
            self.count = count
        if method is not None:
            self.method = method
        if common is not None:
            self.common = common
        self.max_length = max_length
        super(LoremGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        from libs.data_generator.lorem_ipsum import paragraphs, sentence, \
            words
        if self.method == 'w':
            lorem = words(self.count, common=self.common)
        elif self.method == 's':
            lorem = u' '.join([sentence()
                for i in xrange(self.count)])
        else:
            paras = paragraphs(self.count, common=self.common)
            if self.method == 'p':
                paras = ['<p>%s</p>' % p for p in paras]
            lorem = u'\n\n'.join(paras)
        if self.max_length:
            length = random.randint(self.max_length / 10, self.max_length)
            lorem = lorem[:max(1, length)]
        return lorem.strip()


class LoremSentenceGenerator(LoremGenerator):
    method = 's'


class LoremHTMLGenerator(LoremGenerator):
    method = 'p'


class LoremWordGenerator(LoremGenerator):
    count = 7
    method = 'w'


class IntegerGenerator(Generator):
    coerce_type = int
    min_value = - 10 ** 5
    max_value = 10 ** 5

    def __init__(self, min_value=None, max_value=None, *args, **kwargs):
        if min_value is not None:
            self.min_value = min_value
        if max_value is not None:
            self.max_value = max_value
        super(IntegerGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        value = random.randint(self.min_value, self.max_value)
        return value


class SmallIntegerGenerator(IntegerGenerator):
    min_value = -2 ** 7
    max_value = 2 ** 7 - 1


class PositiveIntegerGenerator(IntegerGenerator):
    min_value = 0


class PositiveSmallIntegerGenerator(SmallIntegerGenerator):
    min_value = 0


class ChoiceGenerator(Generator):
    choices = []

    def __init__(self, choices=None, *args, **kwargs):
        if choices is not None:
            self.choices = choices
        super(ChoiceGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        return random.choice(self.choices)


class BooleanGenerator(ChoiceGenerator):
    choices = (True, False)


class NullBooleanGenerator(BooleanGenerator):
    empty_p = 1 / 3.0


class DateTimeGenerator(Generator):
    min_date = datetime.datetime.now() - datetime.timedelta(365 * 5)
    max_date = datetime.datetime.now() + datetime.timedelta(365 * 1)

    def __init__(self, min_date=None, max_date=None, *args, **kwargs):
        if min_date is not None:
            self.min_date = min_date
        if max_date is not None:
            self.max_date = max_date
        assert self.min_date < self.max_date
        super(DateTimeGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        diff = self.max_date - self.min_date
        seconds = random.randint(0, diff.days * 3600 * 24 + diff.seconds)
        return self.min_date + datetime.timedelta(seconds=seconds)


class DateGenerator(Generator):
    min_date = datetime.date.today() - datetime.timedelta(365 * 5)
    max_date = datetime.date.today() + datetime.timedelta(365 * 1)

    def __init__(self, min_date=None, max_date=None, *args, **kwargs):
        if min_date is not None:
            self.min_date = min_date
        if max_date is not None:
            self.max_date = max_date
        assert self.min_date < self.max_date
        super(DateGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        diff = self.max_date - self.min_date
        days = random.randint(0, diff.days)
        date = self.min_date + datetime.timedelta(days=days)
        return date


class DecimalGenerator(Generator):
    coerce_type = Decimal

    max_digits = 24
    decimal_places = 10

    def __init__(self, max_digits=None, decimal_places=None, *args, **kwargs):
        if max_digits is not None:
            self.max_digits = max_digits
        if decimal_places is not None:
            self.decimal_places = decimal_places
        super(DecimalGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        maxint = 10 ** self.max_digits - 1
        value = (
            Decimal(random.randint(-maxint, maxint)) /
            10 ** self.decimal_places)
        return value


class EmailGenerator(StringGenerator):
    chars = string.ascii_lowercase

    def __init__(self, chars=None, max_length=30, tlds=None, *args, **kwargs):
        assert max_length >= 6
        if chars is not None:
            self.chars = chars
        self.tlds = tlds
        super(EmailGenerator, self).__init__(self.chars, max_length=max_length, *args, **kwargs)

    def generate(self):
        maxl = self.max_length - 2
        if self.tlds:
            tld = random.choice(self.tlds)
        elif maxl > 4:
            tld = StringGenerator(self.chars, min_length=3, max_length=3).generate()
        maxl -= len(tld)
        assert maxl >= 2

        name = StringGenerator(self.chars, min_length=1, max_length=maxl-1).generate()
        maxl -= len(name)
        domain = StringGenerator(self.chars, min_length=1, max_length=maxl).generate()
        return '%s@%s.%s' % (name, domain, tld)


class URLGenerator(StringGenerator):
    chars = string.ascii_lowercase
    protocol = 'http'
    tlds = ()

    def __init__(self, chars=None, max_length=30, protocol=None, tlds=None,
        *args, **kwargs):
        if chars is not None:
            self.chars = chars
        if protocol is not None:
            self.protocol = protocol
        if tlds is not None:
            self.tlds = tlds
        assert max_length > (
            len(self.protocol) + len('://') +
            1 + len('.') +
            max([2] + [len(tld) for tld in self.tlds if tld]))
        super(URLGenerator, self).__init__(
            chars=self.chars, max_length=max_length, *args, **kwargs)

    def generate(self):
        maxl = self.max_length - len(self.protocol) - 4 # len(://) + len(.)
        if self.tlds:
            tld = random.choice(self.tlds)
            maxl -= len(tld)
        else:
            tld_max_length = 3 if maxl >= 5 else 2
            tld = StringGenerator(self.chars,
                min_length=2, max_length=tld_max_length).generate()
            maxl -= len(tld)
        domain = StringGenerator(chars=self.chars, max_length=maxl).generate()
        return u'%s://%s.%s' % (self.protocol, domain, tld)


class IPAddressGenerator(Generator):
    coerce_type = unicode

    def generate(self):
        return '.'.join([unicode(part) for part in [
            IntegerGenerator(min_value=1, max_value=254).generate(),
            IntegerGenerator(min_value=0, max_value=254).generate(),
            IntegerGenerator(min_value=0, max_value=254).generate(),
            IntegerGenerator(min_value=1, max_value=254).generate(),
        ]])


class TimeGenerator(Generator):
    def generate(self):
        return datetime.time(
            random.randint(0,23),
            random.randint(0,59),
            random.randint(0,59),
            random.randint(0, 999999),
        )