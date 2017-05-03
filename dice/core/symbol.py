import os
import random
import string
from ..utils import xml_gen


class SymbolBase(object):
    """
    Base class for a symbol object represent a catalog of data to be
    randomized.
    """

    def __init__(self, scope=None, excs=None, exc_types=None):
        """
        :param scope: A list limits the scope of generated results.
        :param excs: A list won't exist in generated results.
        :param exc_types: A list of types won't exist in generated results.
        """
        self.scope = scope
        self.excs = excs
        self.exc_types = exc_types

    def generate(self, alpha=20, beta=1.8):
        """
        Generate a random instance of this symbol without considering scope,
        excs or exc_types. Must be overridden.
        """
        raise NotImplementedError("Method 'generate' not implemented for %s" %
                                  self.__class__.__name__)

    def model(self, alpha=20, beta=1.8):
        """
        Generate a random instance of this symbol.
        """
        if self.scope is None:
            res = self.generate()
            if self.excs is not None:
                while res in self.excs:
                    res = self.generate(alpha, beta)
            return res
        else:
            res = random.choice(self.scope)
            if self.excs is not None:
                while res in self.excs:
                    res = random.choice(self.scope)
            return res


class Bytes(SymbolBase):
    """
    Symbol class for a string contains random bytes (1~255).
    """
    def generate(self, alpha=20, beta=1.8):
        """
        Generate a random bytes string.
        """
        cnt = int(random.weibullvariate(alpha, beta))
        return ''.join(bt for bt in os.urandom(cnt) if bt != b'\x00')


class NonEmptyBytes(Bytes):
    """
    Symbol class for a random byte(1-255) string except empty string.
    """
    def generate(self, alpha=20, beta=1.8):
        """
        Generate a random non-empty bytes string.
        """
        cnt = int(random.weibullvariate(alpha, beta)) + 1
        return ''.join(bt for bt in os.urandom(cnt) if bt != b'\x00')


class String(Bytes):
    """
    Symbol class for a random printable string.
    """
    def generate(self, alpha=20, beta=1.8):
        """
        Generate a random printable string.
        """
        cnt = int(random.weibullvariate(alpha, beta))
        return ''.join(random.choice(string.printable) for _ in range(cnt))


class StringList(SymbolBase):
    """
    Symbol class for a list of random printable strings.
    """
    def __init__(self, scope=None, excs=None, exc_types=None):
        """
        :param scope: A list limits the scope of generated results.
        :param excs: A list won't exist in generated results.
        :param exc_types: A list of types won't exist in generated results.
        """
        super(StringList, self).__init__()
        self.scopes = []
        self.exc_scopes = []
        self.any_scopes = []
        self.excany_scopes = []
        self.required = []

    def generate(self, alpha=20, beta=1.8):
        """
        Generate a random printable strings.
        """
        cnt = int(random.weibullvariate(alpha, beta))
        return ''.join(random.choice(string.printable) for _ in range(cnt))

    def model(self, alpha=3, beta=1.8):
        """
        Generate a random-numbered list contains random printable strings.
        """
        def list_generate():
            scopes = set()
            exc_scopes = set()
            all_not = []
            if len(self.scopes) > 0:
                scopes = set(self.scopes[0][0])
                for sc, _ in self.scopes:
                    scopes &= set(sc)
            else:
                for _ in range(cnt):
                    entry = self.generate()
                    scopes.add(entry)

            if len(self.exc_scopes) > 0:
                for sc, _ in self.exc_scopes:
                    if sc and isinstance(sc[0], str):
                        exc_scopes |= set(sc)
                    elif sc and isinstance(sc[0], list):
                        for listscope in sc:
                            all_not.append(listscope)

            scopes -= exc_scopes
            scopes = list(scopes)
            return scopes, all_not

        def list_check():
            rs = set()
            while scopes:
                flag = True
                rs = set()
                for _ in range(cnt):
                    entry = random.choice(scopes)
                    rs.add(entry)
                for sc, _ in self.any_scopes:
                    if len(sc) > 0 and isinstance(sc[0], str):
                        if rs & set(sc) is None:
                            flag = False
                            break
                    elif sc and isinstance(sc[0], list):
                        pass  # TODO
                for sc, _ in self.excany_scopes:
                    if rs == rs & set(sc):
                        flag = False
                        break
                for sc in all_not:
                    if set(sc) == rs & set(sc):
                        flag = False
                        break
                if flag:
                    break
            return rs

        def list_required(res):
            for requiredsc, _ in self.required:
                res |= set(requiredsc)
            return res

        cnt = int(random.weibullvariate(alpha, beta))

        scopes, all_not = list_generate()

        res = list_check()

        res = list_required(res)

        return list(res)


class Integer(SymbolBase):
    """
    Symbol class for a random integer.
    """
    def __init__(self, scope=None, excs=None, exc_types=None):
        """
        :param scope: A list limits the scope of generated results.
        :param excs: A list won't exist in generated results.
        :param exc_types: A list of types won't exist in generated results.
        """
        super(Integer, self).__init__(scope)
        self.maximum = None
        self.minimum = None

        self.exc_types = []
        if exc_types is not None:
            self.exc_types = exc_types

    def __repr__(self):
        maximum, minimum = self.maximum, self.minimum
        if self.maximum is None:
            maximum = 'Inf'
        if self.minimum is None:
            minimum = '-Inf'
        return '<%s %s~%s>' % (self.__class__.__name__, minimum, maximum)

    def generate(self, alpha=30, beta=1.1):
        """
        Generate a random integer.
        """
        maximum = self.maximum
        minimum = self.minimum
        while True:
            sign = 1.0 if random.random() > 0.5 else -1.0
            res = sign * (2.0 ** (random.weibullvariate(alpha, beta)) - 1.0)
            if maximum is not None:
                if maximum >= 0 and res > maximum + 1:
                    continue
                if maximum < 0 and res > maximum:
                    continue
            if minimum is not None:
                if minimum >= 0 and res < minimum:
                    continue
                if minimum < 0 and res < minimum - 1:
                    continue
            return int(res)


class Xml(SymbolBase):
    """
        Symbol class for xml.
        """

    def __init__(self, scope=None, excs=None, exc_types=None):
        """
        :param scope: A list limits the scope of generated results.
        :param excs: A list won't exist in generated results.
        :param exc_types: A list of types won't exist in generated results.
        """
        super(StringList, self).__init__()
        self.base = str()

    def generate(self, alpha=20, beta=1.8):
        """
        Generate a random printable strings.
        """
        try:
            os.makedirs('xml/')
        except:
            pass
        nst = String()
        fname = 'xml/' + self.base + nst.generate(5) + '.xml'
        f = open(fname, 'w')
        f.write(xml_gen.RngUtils(self.base))
        f.close()
        return fname

    def model(self, alpha=3, beta=1.8):
        """
        Generate a random-numbered list contains random printable strings.
        """
        if self.scope is None:
            res = self.generate()
            if self.excs is not None:
                while res in self.excs:
                    res = self.generate(alpha, beta)
            return res
        else:
            res = random.choice(self.scope)
            if self.excs is not None:
                while res in self.excs:
                    res = random.choice(self.scope)
            return res
