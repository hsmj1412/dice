import os
import random
import string


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
        cnt = int(random.weibullvariate(alpha, beta))
        res = set()
        scopes = set()
        exc_scopes = set()
        all_not = []
        if self.scopes:
            scopes = set(self.scopes[0][0])
            for scope, _ in self.scopes:
                scopes &= set(scope)
        else:
            for _ in range(cnt):
                entry = self.generate()
                scopes.add(entry)

        if self.exc_scopes:
            for scope, _ in self.exc_scopes:
                if scope and isinstance(scope[0], str):
                    exc_scopes |= set(scope)
                elif scope and isinstance(scope[0], list):
                    for listscope in scope:
                        all_not.append(listscope)

        scopes -= exc_scopes
        scopes = list(scopes)

        while scopes:
            flag = True
            res = set()
            for _ in range(cnt):
                entry = random.choice(scopes)
                res.add(entry)
            for scope, _ in self.any_scopes:
                if scope and isinstance(scope[0], str):
                    if res & set(scope) is None:
                        flag = False
                        break
                elif scope and isinstance(scope[0], list):
                    pass  # TODO
            for scope, _ in self.excany_scopes:
                if res == res & set(scope):
                    flag = False
                    break
            for scope in all_not:
                if set(scope) == res & set(scope):
                    flag = False
                    break
            if flag:
                break

        for requiredsc, _ in self.required:
            res |= set(requiredsc)

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
