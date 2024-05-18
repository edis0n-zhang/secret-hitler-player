
#Note -- prompt logic given at the bottom of the file

def generate_startup_prompt(role, db):
    prompt = f'You are playing the board game “Secret Hitler.” You will be playing a game with 7 total players. 
    The role you have been chosen for this game is: {role}. You must wait your turn before committing an action. 
    It is not yet your turn. When it is your turn, you will be informed of the current state of the game and the
    history of moves made. You will be reminded of your previously chosen strategy and your opinions of other players, 
    which you can update throughout the game. When a president chooses a chancellor, there will be three rounds of discussion,
    and each player will have a “turn” to speak in each discussion. Your goal during discussion is to further the strategy you
    have specified to yourself, convince other players to your side, and gather more information on the other players. Thus you
    will generate a short speech to other players to further this agenda. Otherwise, if it is your turn and you must complete an
    action (vote yes or no to a president/chancellor, pick someone to be chancellor, enact a policy, execute special power),
    simply reference the information available to you, and choose one action. There is nothing to be done at this moment.
    You will be prompted when it is your turn. For reference, here are the rules of the game: {db["rules"]}'
    return prompt


def generate_action_prompt(game_state, previous_strategy, player_beliefs, turn, role, previous_conversation=None, previous_action=None):
    prompt = f'It is your turn. You will receive the current state of the game, history of moves made, 
    and be reminded of your previously chosen strategy and opinions of other players.\n'
    prompt += f'Currently, policies have been enacted in the following order:\n {game_state["policies_enacted"]}.'
    prompt += f'Currently, the president is {game_state["president"]} and the chancellor is {game_state["chancellor"]}.'
    prompt += f'The presiedent and chancellor are in state: {game_state["president_chancellor_state"]}.\n'
    if previous_conversation:
        prompt += f'There has been new conversation since your last turn: {previous_conversation}.'
    prompt += f'On your last move, you chose to {previous_action}, following strategy {previous_strategy}.'
    prompt += f'Your beliefs about the other players are as follows: {player_beliefs}'

    prompt += f'Now, you must complete your action. Recall that the action you must take is {turn} and your role is {role}. First, please describe what your strategy is for this current move. Your future self will reference this strategy on the next turn when deciding what to do.\n'
    if turn == 'discuss':
        prompt += f'Your action to complete is discuss. You are on round {game_state["round"]} of discussing. Please keep your response direct and to the point. Convince the others to follow your strategy, but do not reveal anything that would hurt you.'
    elif turn == 'vote':
        prompt += f'Your action is to vote. You must choose yes or no for the current nominated president and chancellor. Respond to this with only one word: YES or NO.'
    elif turn == 'remove policy':
        if game_state["role"] == 'chancellor':
            prompt += f'As {role}, you have been given 2 cards: Card 1: {game_state["card_1"]}, Card 2: {game_state["card_2"]}. You must pick one to discard, and one to enact as policy. Respond to this with the card to DISCARD: 1, 2, 3. Respond with just the number you choose, and no other text.'
        elif game_state["role"] == 'president':
            prompt += f'As president, you have drawn 3 cards: Card 1: {game_state["card_1"]}, Card 2: {game_state["card_2"]}, Card 3: {game_state["card_3"]}. Respond to this with the card you choose to DISCARD. Simply give a number—1, 2, or 3. Do not respond with any other text.'
    elif turn == 'pick chancellor':
        prompt += f'As president, you must choose a chancellor. The available chancellors to pick are {game_state["chancellor_options"]}. Select one player to be your chancellor. Respond to this with the name of the player. Example for choosing player 1: “PLAYER 1”. Don\'t include any other text besides the player name.'
    elif turn == 'execute special power':
        prompt += f'Choose someone to {game_state["special_power_description"]}. The available people to do this to are {game_state["special_power_options"]}. Respond to this with the name of the player that you choose. Example: “PLAYER 1”. Don\'t include any text besides that.'
    
    return prompt


#Prompt Logic Part 1: Startup the game
"""
You are playing the board game “Secret Hitler.” You will be playing a game with 7 total players. 

The role you have been chosen for this game is: [ROLE]

You must wait your turn before committing an action. It is not yet your turn. When it is your turn, 
you will be informed of the current state of the game and the history of moves made. You will be reminded
of your previously chosen strategy and your opinions of other players, which you can update throughout the game.

When a president chooses a chancellor, there will be three rounds of discussion, and each player will have a 
“turn” to speak in each discussion. Your goal during discussion is to further the strategy you have specified 
to yourself, convince other players to your side, and gather more information on the other players. Thus you 
will generate a short speech to other players to further this agenda.

Otherwise, if it is your turn and you must complete an action (vote yes or no to a president/chancellor, pick 
someone to be chancellor, enact a policy, execute special power), simply reference the information available to you, 
and choose one action.

There is nothing to be done at this moment. You will be prompted when it is your turn For reference, here are the rules of the game: [RULES].

"""

#Prompt Logic Part 2: Action Prompt
"""

It is your turn. You will receive the current state of the game, history of moves made, and be reminded of your previously chosen strategy and opinions of other players.

Currently, policies have been enacted in the following order:
    A [Policy X] card was enacted by [Player Y] on [Round Z].
    A [Policy X] card was enacted by [Player Y] on [Round Z].

Currently, the president is [Player A] and the chancellor is [Player B]. They're current state is [STATE B].

For your turn, the action you must complete is [ACTION].

[If conversation happened since you last spoke]
    There has been new conversation since you last spoke.
    [PLAYER A] said: [PLAYER A TEXT]
    [PLAYER B] said: [PLAYER B TEXT]

On your last turn, you made this move: [MOVE A], and described your strategy to be:
    [STRATEGY] (in a dict)

This is what your previous beliefs were on all the players: (in form of a dict)
    [Player A]: [Beliefs]
    [Player B]: [Beliefs]


Now, you must complete your action. Recall that the action you must take is [ACTION] and your role is [ROLE]. First, please describe what your strategy is for this current move. Your future self will reference this strategy on the next turn when deciding what to do. 

- [If turn == discuss]
    
    Your action to complete is **discuss**, and you are on your [#]th round of discussing. Please keep your response direct and to the point. Convince the others to follow your strategy, but do not reveal anything that would hurt you.
    
- [If turn == vote]
    
    Your action is to **vote**. You must choose yes or no for the current nominated president and chancellor. Respond to this with only one word: YES or NO. 
    
- [If turn == remove policy]
    
    [If chancellor]:
    
    As chancellor, you have been given 2 cards: Card 1: [CARD 1], Card 2: [CARD 2]. You must pick one to discard, and one to enact as policy. Respond to this with the card to DISCARD: 1, 2, 3. Respond with just the number you choose, and no other text.
    
    [If president]:
    
    As president, you have drawn 3 cards: Card 1: [CARD], Card 2: [CARD], Card 3: [CARD]. Respond to this with the card you choose to DISCARD. Simply give a number—1, 2, or 3. Do not respond with any other text.
    
- [If turn == pick chancellor]
    
    As president, you must choose a chancellor. The available chancellors to pick are [LIST OF PLAYERS]. Select one player to be your chancellor. Respond to this with the name of the player. Example for choosing player 1: “PLAYER 1”. Don’t include any other text besides the player name.
    
- [If turn == execute special power]
    
    Choose someone to [SPECIAL POWER DESCRIPTION]. The available people to do this to are: [LIST OF PLAYERS]. Respond to this with the name of the player that you choose. Example: “PLAYER 1”. Don’t include any text besides that.

"""