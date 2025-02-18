import difflib
import string

from int.proof_system.all_axioms import all_axioms_to_prove
from int.representation import base
from int.visualization import seq_parse
from int.visualization.seq_parse import entity_to_seq_string

theorem_names = [theorem.name for theorem in list(all_axioms_to_prove.values())]

thm2index = {
    node: ind
    for ind, node in enumerate(theorem_names)
}
index2thm = {
    ind: node for ind, node in enumerate(theorem_names)
}

CONDITION_LEXEME = '&'
OBJECTIVE_LEXEME = '#'
PADDING_LEXEME = '_'
EOS_LEXEME = '$'
OUTPUT_START_LEXEME = '@'
BOS_LEXEME = '?'

ADD_CHAR_LEXEME = '[+]'
REMOVE_CHAR_LEXEME = '[-]'

MULTI_CHAR_LEXEMES = [
    '1/',
    '^2',
    'sqrt',
    r'\leq ',
    r'\geq ',
    ADD_CHAR_LEXEME,
    REMOVE_CHAR_LEXEME
    # We haven't use inequalities in INT yet, so not sure if '\leq' and '\geq'
    # work properly.
]

VOCABULARY = (
        [
            BOS_LEXEME,
            PADDING_LEXEME,
            EOS_LEXEME,
            OUTPUT_START_LEXEME,
            OBJECTIVE_LEXEME,
            CONDITION_LEXEME,
            '=',
            '(',
            ')',
            '*',
            '+',
            '0',
            '1',
            '-',  # both subtraction and unary minus
        ] +
        list(string.ascii_lowercase) +
        MULTI_CHAR_LEXEMES
)

AXIOM_TOKENS = [char for char in 'ABCDEFGHIJKLMNOPQR']
AXIOM_TO_CHAR = {axiom: char for axiom, char in zip(theorem_names, AXIOM_TOKENS)}
CHAR_TO_AXIOM = {char: axiom for axiom, char in zip(theorem_names, AXIOM_TOKENS)}

AXIOM_LENGTH = {'O': 2, 'D': 1, 'H': 1, 'A': 1, 'J': 1, 'L': 3, 'F': 1, 'I': 1, 'B': 1, 'K': 1, 'Q': 2, 'E': 1, 'C': 1, 'G': 1, 'N': 1, 'P': 2, 'R': 2, 'M': 2}

POINTER_SYMBOLS = [
    '~',
    '!',
    ';',
]

POLICY_VOCABULARY = (VOCABULARY + AXIOM_TOKENS + POINTER_SYMBOLS)


TOKEN_TO_STR = dict(list(enumerate(POLICY_VOCABULARY)))
STR_TO_TOKEN = {str_: token for token, str_ in TOKEN_TO_STR.items()}
assert len(TOKEN_TO_STR) == len(STR_TO_TOKEN), \
    "There are some duplicated lexemes in vocabulary."
assert STR_TO_TOKEN[BOS_LEXEME] == 0
assert STR_TO_TOKEN[PADDING_LEXEME] == 1
assert STR_TO_TOKEN[EOS_LEXEME] == 2
assert STR_TO_TOKEN[OUTPUT_START_LEXEME] == 3
assert len(TOKEN_TO_STR) == 68

class EntityMask:
    def __init__(self, entity, left_str, right_str):
        self.entity = entity
        self.left_str = left_str
        self.right_str = right_str
        self.interior = 'None'

    def add_interior(self, interior):
        self.interior = interior

    def mask(self):
        return self.left_str + self.interior + self.right_str

def generate_masks_for_logic_statement(logic_statement, symbol='~'):
    if logic_statement.name.startswith("BiggerOrEqual"):
        operator = '\geq '
    elif logic_statement.name.startswith("SmallerOrEqual"):
        operator = '\leq '
    else:
        operator = '='

    first_operand = logic_statement.operands[0]
    second_operand = logic_statement.operands[1]
    first_operand_str = entity_to_seq_string(first_operand)
    second_operand_str = entity_to_seq_string(second_operand)

    first_operand_mask = EntityMask(first_operand, '',
                                    operator + second_operand_str)
    second_operand_mask = EntityMask(second_operand, first_operand_str+operator, '')
    operands_with_mask_queue = [first_operand_mask, second_operand_mask]
    all_masks = [first_operand_mask, second_operand_mask]
    while len(operands_with_mask_queue) > 0:
        current_operand = operands_with_mask_queue.pop()
        parse_mask_for_entity(current_operand, operands_with_mask_queue, all_masks, symbol)


    entity_to_mask = {mask.entity : mask.mask() for mask in all_masks}
    mask_to_entity = {mask.mask(): mask.entity for mask in all_masks}

    return entity_to_mask, mask_to_entity


def parse_mask_for_entity(entity_with_mask, operands_with_mask_queue,  all_masks, symbol):
    entity = entity_with_mask.entity
    left_str = entity_with_mask.left_str
    right_str = entity_with_mask.right_str
    entity_name = entity_with_mask.entity.name

    entity_type = None
    if entity_name.startswith("add"):
        entity_type = '+'
    elif entity_name.startswith("sub"):
        entity_type = '-'
    elif entity_name.startswith("mul"):
        entity_type = '*'

    if entity_type in {'+', '-', '*'}:
        first_operand = entity.operands[0]
        second_operand = entity.operands[1]
        first_operand_str = entity_to_seq_string(first_operand)
        second_operand_str = entity_to_seq_string(second_operand)
        first_operand_mask = EntityMask(first_operand, left_str + '(', entity_type + second_operand_str + ')' + right_str)
        second_operand_mask = EntityMask(second_operand, left_str + '(' + first_operand_str + entity_type, ')' + right_str)

        entity_with_mask.add_interior('(' + first_operand_str + entity_type + symbol + second_operand_str + ')')
        operands_with_mask_queue.append(first_operand_mask)
        operands_with_mask_queue.append(second_operand_mask)
        all_masks.append(first_operand_mask)
        all_masks.append(second_operand_mask)

    elif entity_name.startswith("opp"):
        operand = entity.operands[0]
        operand_str = entity_to_seq_string(operand)
        operand_mask = EntityMask(operand, left_str + '(-', ')' + right_str)
        entity_with_mask.add_interior('(-' + symbol + operand_str + ')')
        operands_with_mask_queue.append(operand_mask)
        all_masks.append(operand_mask)

    elif entity_name.startswith("sqr"): #done
        operand = entity.operands[0]
        operand_str = entity_to_seq_string(operand)
        operand_mask = EntityMask(operand, left_str + '(', '^2)' + right_str)
        entity_with_mask.add_interior('('+operand_str + '^2'+symbol+')')
        operands_with_mask_queue.append(operand_mask)
        all_masks.append(operand_mask)

    elif entity_name.startswith("sqrt"):
        operand = entity.operands[0]
        operand_str = entity_to_seq_string(operand)
        operand_mask = EntityMask(operand, left_str + '(sqrt', ')' + right_str)
        entity_with_mask.add_interior('(sqrt' + symbol  + operand_str + ')')
        operands_with_mask_queue.append(operand_mask)
        all_masks.append(operand_mask)

    elif entity_name.startswith("inv"):
        operand = entity.operands[0]
        operand_str = entity_to_seq_string(operand)
        operand_mask = EntityMask(operand, left_str + '(1/', ')' + right_str)
        entity_with_mask.add_interior('(1/' + symbol + operand_str + ')')
        operands_with_mask_queue.append(operand_mask)
        all_masks.append(operand_mask)
    else:
        entity_str = entity_to_seq_string(entity)
        entity_mask = EntityMask(entity, left_str, right_str)
        entity_with_mask.add_interior(entity_str + symbol)
        all_masks.append(entity_mask)
        entity_mask.add_interior(entity_str + symbol)

def split_expression_on_lexeme(expr, lexeme):
    subexprs = []
    expr_beg = 0

    lexeme_beg = expr.find(lexeme, expr_beg)
    while lexeme_beg != -1:
        if lexeme_beg > expr_beg:
            subexprs.append(expr[expr_beg:lexeme_beg])

        lexeme_end = lexeme_beg + len(lexeme)
        subexprs.append(expr[lexeme_beg:lexeme_end])

        expr_beg = lexeme_end
        lexeme_beg = expr.find(lexeme, expr_beg)

    if expr_beg < len(expr):
        subexprs.append(expr[expr_beg:])

    return subexprs


def split_formula_to_lexemes(formula):
    subexprs = [formula]
    # We split the formula on every occurrence of any MULTI_CHAR_LEXEME
    for lexeme in MULTI_CHAR_LEXEMES:
        next_subexprs = []
        for subexpr in subexprs:
            next_subexprs += (
                [subexpr] if subexpr in VOCABULARY
                else split_expression_on_lexeme(subexpr, lexeme)
            )
        subexprs = next_subexprs

    lexemes = []
    for subexpr in subexprs:
        lexemes += (
            [subexpr] if subexpr in VOCABULARY
            else list(subexpr)  # treat every char as a separate lexeme
        )
    return lexemes


class ActionRepresentationPointer:
    def __init__(self, vanilla=False):
        self.vanilla = vanilla

    token_consts = base.TokenConsts(
        num_tokens=len(STR_TO_TOKEN),
        padding_token=STR_TO_TOKEN[PADDING_LEXEME],
        output_start_token=STR_TO_TOKEN[OUTPUT_START_LEXEME],
    )

    @staticmethod
    def proof_state_to_input_formula(state):
        conditions = [
            seq_parse.logic_statement_to_seq_string(condition)
            for condition in state['observation']['ground_truth']
        ]
        # must be only one objective
        objectives = [
            seq_parse.logic_statement_to_seq_string(objective)
            for objective in state['observation']['objectives']
        ]
        formula = OBJECTIVE_LEXEME + OBJECTIVE_LEXEME.join(objectives)
        condition = CONDITION_LEXEME
        if len(conditions) > 0:
            condition += CONDITION_LEXEME.join(conditions)
        return formula, condition

    @staticmethod
    def find_diff(current_state_str, destination_state_str):

        expressions_to_change = {
            '1/': '~',
            '^2': '!',
            '\geq ' : '%',
            '\leq ' : ';'
        }
        for expression, target in expressions_to_change.items():
            current_state_str = current_state_str.replace(expression, target)
            destination_state_str = destination_state_str.replace(expression, target)

        diff = difflib.ndiff(current_state_str, destination_state_str)
        input_formula = [x for x in current_state_str]
        for i, s in enumerate(diff):
            if s[0] == ' ':
                continue
            elif s[0] == '-':
                input_formula[i] = f'{REMOVE_CHAR_LEXEME}{input_formula[i]}'
            elif s[0] == '+':
                input_formula.insert(i, f'{ADD_CHAR_LEXEME}{s[-1]}')

        formula = ''.join(input_formula)
        for expression, target in expressions_to_change.items():
            formula = formula.replace(target, expression)

        return formula


    def proof_states_to_policy_input_formula(self, current_state, destination_state, vanilla=False):
        current_str, condition = self.proof_state_to_input_formula(current_state)
        destination_objective = OBJECTIVE_LEXEME
        if isinstance(destination_state, str):
            destination_objective += destination_state
        else:
            destination_objective += seq_parse.logic_statement_to_seq_string(destination_state['observation']['objectives'][0])
        if not self.vanilla and not vanilla:
            formula = self.find_diff(current_str, destination_objective)
        else:
            formula = current_str
        formula += condition
        formula += EOS_LEXEME
        return formula


    @classmethod
    def proof_state_to_tokenized_objective(cls, state):
        state_objective = [seq_parse.logic_statement_to_seq_string(objective)
                                  for objective in state['observation']['objectives']
                                  ][0]
        return cls.tokenize_formula(state_objective)

    @classmethod
    def proof_step_and_action_to_formula(cls, proof_step, action):
        '''this version of code assumes there is exactly one objective'''
        objective = proof_step['observation']['objectives'][0]
        return cls.action_to_formula(objective, action)


    @classmethod
    def action_to_formula(cls, objective, action):
        '''This version of code assumes there is exactly one objective'''
        if isinstance(action[0], int):
            used_axiom = index2thm[action[0]]
            entities_used = [objective.ent_dic[idx] for idx in action[1:]]
        else:
            used_axiom = action[0]
            entities_used = action[1:]
        formula = OUTPUT_START_LEXEME + AXIOM_TO_CHAR[used_axiom]
        entity_to_mask, mask_to_entity = generate_masks_for_logic_statement(objective, symbol='~')
        masks = [entity_to_mask[entity] for entity in entities_used]
        formula += cls.merge_masks(masks) + EOS_LEXEME
        return formula

    @staticmethod
    def merge_masks(masks):
        if len(masks) > 1:
            pointers = [0, 0, 0]
            out_str = ''
            while pointers[0] < len(masks[0]):
                chars = []
                for i in range(len(masks)):
                    if pointers[i] < len(masks[i]):
                        chars.append(masks[i][pointers[i]])
                    else:
                        chars.append('_')
                found_special = False
                for j, char in enumerate(chars):
                    if char == '~':
                        out_str += POINTER_SYMBOLS[j]
                        pointers[j] += 1
                        found_special = True
                if not found_special:
                    out_str += chars[0]
                    for j in range(len(masks)):
                        pointers[j] += 1

        else:
            return masks[0]
        return out_str

    @staticmethod
    def tokenize_formula(formula):
        lexemes = split_formula_to_lexemes(formula)
        try:
            return [STR_TO_TOKEN[lexeme] for lexeme in lexemes]
        except KeyError as e:
            raise ValueError("Tokenization error - unrecognized lexeme \n Formula split to lexemes:\n{lexemes}")


    @staticmethod
    def formula_from_tokens(tokens):
        return "".join(TOKEN_TO_STR[token] for token in tokens)

    @staticmethod
    def action_from_char(char):
        if char in CHAR_TO_AXIOM:
            return CHAR_TO_AXIOM[char]
        else:
            return None

    @classmethod
    def pointer_str_to_action(cls, objective, action_str, mode='idx'):
        action_raw = cls.split_pointer_action_str(action_str)
        assert action_raw is not None, 'Improperly decoded action string'
        _, mask_to_entity = generate_masks_for_logic_statement(objective)
        action = [action_raw[0]]
        for entity_str in action_raw[1:]:
            if entity_str in mask_to_entity:
                action.append(mask_to_entity[entity_str])
            else:
                raise ValueError(f'Unrecognized entity: {entity_str}')

        if mode == 'idx':
            action[0] = thm2index[action[0]]
            for i in range(1, len(action)):
                action[i] = action[i].index

        return tuple(action)

    @staticmethod
    def split_pointer_action_str(action_str):
        if action_str[0] != '@' or action_str[-1:] != '$':
            raise ValueError('Invalid prediction format')
        prediction_str = action_str[1:-1]
        if len(prediction_str) == 0:
            return None

        if prediction_str[0] in CHAR_TO_AXIOM:
            axiom = CHAR_TO_AXIOM[prediction_str[0]]
            axiom_len = AXIOM_LENGTH[prediction_str[0]]
            input_entities_raw = [prediction_str[1:] for _ in range(axiom_len)]
            input_entities_str = []
            for num in range(len(input_entities_raw)):
                entity_str = input_entities_raw[num]
                pointer_symbol = POINTER_SYMBOLS[num]
                for different_pointer_symbol in POINTER_SYMBOLS:
                    if different_pointer_symbol != pointer_symbol:
                        entity_str = entity_str.replace(different_pointer_symbol, '')
                entity_str = entity_str.replace(pointer_symbol, POINTER_SYMBOLS[0])
                input_entities_str.append(entity_str)
            return [axiom, *input_entities_str]
        else:
            return None