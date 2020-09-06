"""

"""

from functools import partial
import lark
from utils import utils, constants as c


class ListingTransformer(lark.Transformer):
    """
    Transforms content parsed by grammar_listing.lark further.
    Used for the developer and inspirations list.
    """

    def unquoted_value(self, x):
        return x[0].value

    def quoted_value(self, x):
        return x[0].value[1:-1]  # remove quotation marks

    def property(self, x):
        """
        The key of a property will be converted to lower case and the value part is the second part
        :param x:
        :return:
        """
        return x[0], x[1:]

    def name(self, x):
        """
        The name part is treated as a property with key "Name"
        :param x:
        :return:
        """
        return 'Name', x[0].value

    def entry(self, x):
        """
        All (key, value) tuples are inserted into a dictionary.
        :param x:
        :return:
        """
        d = {}
        for key, value in x:
            if key in d:
                raise RuntimeError('Key in entry appears twice')
            d[key] = value
        return d

    def start(self, x):
        return x


# transformer
class EntryTransformer(lark.Transformer):

    def unquoted_value(self, x):
        return x[0].value

    def quoted_value(self, x):
        return x[0].value[1:-1]  # remove quotation marks

    def property(self, x):
        """
        The key of a property will be converted to lower case and the value part is the second part
        :param x:
        :return:
        """
        return x[0], x[1:]

    def title(self, x):
        return 'Title', x[0].value

    def note(self, x):
        """
        Optional
        :param x:
        :return:
        """
        if not x:
            raise lark.Discard
        return 'Note', ''.join((x.value for x in x))

    def building(self, x):
        d = {}
        for key, value in x:
            if key in d:
                raise RuntimeError('Key in entry appears twice')
            d[key] = value
        return 'Building', d

    def start(self, x):
        # we do the essential fields and valid fields checks right here
        fields = [x[0] for x in x]
        # check for essential fields
        for field in c.essential_fields:
            if field not in fields:
                raise RuntimeError('Essential field "{}" is missing'.format(field))
        # check for valid fields (in that order)
        index = 0
        for field in fields:
            while index < len(c.valid_fields) and field != c.valid_fields[index]:
                index += 1
            if index == len(c.valid_fields):
                raise RuntimeError('Field "{}" either not valid or in wrong order'.format(field))
        d = {}
        for key, value in x:
            if key in d:
                raise RuntimeError('Key in entry appears twice')
            d[key] = value
        return d


def parse(parser, transformer, content):
    tree = parser.parse(content)
    value = transformer.transform(tree)
    return value


def create(grammar, Transformer):
    parser = lark.Lark(grammar, debug=False, parser='lalr')
    transformer = Transformer()
    return partial(parse, parser, transformer)


def read_and_parse(content_file: str, grammar_file: str, Transformer: lark.Transformer):
    """
    Reads a content file and a grammar file and parses the content with the grammar following by
    transforming the parsed output and returning the transformed result.
    :param content_file:
    :param grammar_file:
    :param transformer:
    :return:
    """
    grammar = utils.read_text(grammar_file)
    parse = create(grammar, Transformer)

    content = utils.read_text(content_file)
    return parse(content)