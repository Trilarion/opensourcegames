"""
This is for reading game entries, inspirations and developers with the help of a grammar
defined in lark.
"""

from functools import partial
import lark

from utils import utils as u


class ListingTransformer(lark.Transformer):
    """
    Transforms content parsed by grammar_listing.lark further.
    Used for the developer and inspirations list.
    """

    def unquoted_value(self, x):
        """
        Value without quotes
        """
        return str(x[0]).strip()  # strip whitespaces

    def quoted_value(self, x):
        """
        Value with quotes "", remove them.
        """
        return str(x[0])[1:-1].strip()  # remove quotation marks and strip whitespaces

    def property(self, x):
        """
        A property is a line of the format: fieldname: content list
        Key is first part, values are following.
        """
        return str(x[0]).strip(), x[1:]

    def name(self, x):
        """
        The very first line is the name part
        It is treated as a property with key "Name"
        """
        return 'Name', str(x[0]).strip()

    def entry(self, x):
        """
        All (key, value) tuples are inserted into a dictionary.
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
    """
    Transformer on an entry
    """

    def unquoted_value(self, x):
        """
        Value without quotes
        """
        return str(x[0]).strip()  # remove whitespaces

    def quoted_value(self, x):
        """
        Value with quotes "", remove them.
        """
        return str(x[0])[1:-1].strip()  # remove quotation marks and whitespaces

    def comment_value(self, x):
        """
        Comment in parentheses, remove them.
        """
        return str(x[0])[1:-1].strip()  # remove parenthesis

    def value(self, x):
        """
        This also stores the comment if existing.
        """
        if len(x) == 1:
            v = str(x[0])
        else:
            v = Value(*x)
        return v

    def property(self, x):
        """
        A property is a line of the format: fieldname: content list
        The key of a property will be converted to lower case and the value part is the second part
        """
        return str(x[0]).strip(), x[1:]

    def title(self, x):
        """
        Title of the game, i.e. the first line in an entry.
        """
        return 'Title', x[0].strip()

    def note(self, x):
        """
        Optional the lines after the fields and before the building section.
        """
        x = ''.join(x).strip()
        if not x:
            raise lark.Discard
        return 'Note', x

    def building(self, x):
        """
        Returns the whole building section
        """
        return 'Building', x

    def start(self, x):
        """
        The initial section
        """
        return x


class Value(str):
    """
    A value is a string with an additional meta-object (a comment) but mostly behaves like a string. It was needed because
    it occurred naturally in field entries. However, deriving from str maybe wasn't the best idea (although also not the
    worst).
    """

    def __new__(cls, value, comment=None):
        obj = str.__new__(cls, value)
        obj.comment = comment
        return obj


def parse(parser, transformer, content):
    """
    Given and parser and a transformer and some content, first applies the parser on the content to obtain a parsed
    tree, then applies the transformer to transform (consume) the tree into our desired output structure.
    """
    tree = parser.parse(content)
    value = transformer.transform(tree)
    return value


def create(grammar, Transformer):
    """
    Given a grammar and a transformer class, creates a parser corresponding to the grammar, instantiates the transformer
    and returns a function that can call the parser and transformer on some content.
    """
    parser = lark.Lark(grammar, debug=False, parser='lalr')
    transformer = Transformer()
    return partial(parse, parser, transformer)


def read_and_parse(content_file: str, grammar_file: str, Transformer: lark.Transformer):
    """
    Reads a content file and a grammar file and parses the content with the grammar following by
    transforming the parsed output and returning the transformed result.
    Is efficient if only a single file needs to be read in total. Otherwise, one could reuse the grammar and transformer.
    """
    grammar = u.read_text(grammar_file)
    parse = create(grammar, Transformer)

    content = u.read_text(content_file)
    return parse(content)