"""
Service layer for GPT-2 text generation of conversation starters.

This module houses the ConversationGenerator class which initializes a causal HuggingFace 
language model (GPT-2) and guides it via prompt steering to generate contextual 
icebreakers. It includes a rule-based template fallback mechanism if the neural model 
fails to load or execute.
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)

# Template-based starters for fallback generation
FALLBACK_TEMPLATES = [
    "How do you think {theme} is shaping the future of {interest}?",
    "What trends in {theme} or {interest} are you most excited about lately?",
    "Are you working on any projects that integrate {theme} with {interest}?",
    "What brought you to this event on {theme}, and what are you hoping to learn?",
    "How do you see the intersection of {theme} and {interest} evolving in the next few years?"
]

class ConversationGenerator:
    """
    Service that uses GPT-2 to generate exactly 3 professional conversation starters
    tailored to the event description, themes, and user interests.
    """
    def __init__(self, model_name: str = "gpt2"):
        """
        Initializes the ConversationGenerator with the designated model name.

        Args:
            model_name (str, optional): The HuggingFace identifier for the causal LLM. Defaults to "gpt2".
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self._initialized = False

    def initialize_model(self) -> bool:
        """
        Lazily loads the HuggingFace tokenizer and model.
        Sets a deterministic generation seed (42) for testing consistency.

        Returns:
            bool: True if the model and tokenizer load successfully, False otherwise.
        """
        if self._initialized:
            return True
        try:
            logger.info(f"Loading conversation generation model: {self.model_name}...")
            # Import transformers here to avoid blocking startup
            from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # GPT-2 has no pad token, set it to EOS token to avoid warnings
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            set_seed(42)
            self._initialized = True
            logger.info("Conversation generation model loaded successfully.")
            return True
        except Exception as e:
            logger.warning(
                f"Failed to load generator model {self.model_name}: {e}. "
                "ConversationGenerator will fall back to template-based generation."
            )
            self.tokenizer = None
            self.model = None
            self._initialized = False
            return False

    def generate_starters(
        self, 
        event_description: str, 
        themes: List[str], 
        interests: str,
        num_starters: int = 3
    ) -> List[str]:
        """
        Generates conversation starters using GPT-2. Falls back to pre-defined
        templates if the model fails or outputs poorly formatted text.

        Args:
            event_description (str): Description or title of the networking event.
            themes (List[str]): List of key themes extracted from the event description.
            interests (str): User-specified personal or professional interest strings.
            num_starters (int, optional): The target count of starters to generate. Defaults to 3.

        Returns:
            List[str]: Exactly `num_starters` conversation starters.
        """
        themes_str = ", ".join(themes) if themes else "Networking"
        
        # Load model if possible
        model_loaded = self.initialize_model()

        if model_loaded and self.model is not None and self.tokenizer is not None:
            try:
                # Construct a strict few-shot prompt to steer GPT-2 output
                prompt = self._build_prompt(event_description, themes_str, interests)
                
                # Encode input
                inputs = self.tokenizer(prompt, return_tensors="pt")
                input_length = inputs.input_ids.shape[1]
                
                # Generate text
                import torch
                with torch.no_grad():
                    output_ids = self.model.generate(
                        **inputs,
                        max_new_tokens=150,
                        do_sample=True,
                        temperature=0.8,
                        top_k=50,
                        top_p=0.92,
                        repetition_penalty=1.2,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                
                # Decode output
                generated_text = self.tokenizer.decode(output_ids[0][input_length:], skip_special_tokens=True)
                
                # Parse generated starters
                starters = self._parse_starters(generated_text)
                
                if len(starters) >= num_starters:
                    return starters[:num_starters]
                
                logger.warning(
                    f"GPT-2 generated fewer starters ({len(starters)}) than expected. "
                    "Supplementing with templates."
                )
                
            except Exception as e:
                logger.error(f"Error during neural generation: {e}. Executing template-based fallback...")
                
        return self._generate_fallback(themes, interests, num_starters)

    def _build_prompt(self, event_description: str, themes_str: str, interests_str: str) -> str:
        """
        Builds the few-shot prompt for GPT-2 to ensure structured questions output.

        Args:
            event_description (str): Target event description.
            themes_str (str): Themes formatted as a string.
            interests_str (str): User interests formatted as a string.

        Returns:
            str: Compiled prompt.
        """
        return f"""You are a professional networking coach. Generate exactly 3 conversation starters for a networking event.
 
Event: AI for Sustainable Cities
Themes: AI, Sustainability, Urban Planning
Interests: Climate Change, Urban Planning
Conversation Starters:
- How do you think AI can improve sustainable urban planning?
- What innovations in smart cities interest you most?
- Have you seen any AI applications making cities greener?
 
Event: Biotech and Medicine Summit
Themes: Healthcare, Technology, Innovation
Interests: Drug Discovery, Cancer Research
Conversation Starters:
- What impact do you think biotechnology will have on drug discovery in the next decade?
- How are you hoping technology will accelerate cancer research?
- What specific medical innovations at this summit are you excited to learn about?
 
Event: {event_description}
Themes: {themes_str}
Interests: {interests_str}
Conversation Starters:
-"""

    def _parse_starters(self, text: str) -> List[str]:
        """
        Extracts starters from the raw generated text completion.

        Args:
            text (str): Decoder generated text completion block.

        Returns:
            List[str]: Parsed list of extracted question sentences.
        """
        starters = []
        # Prepend a bullet to capture the first generated starter (since the prompt ends with -)
        full_generation = "-" + text
        
        # Split on line breaks
        lines = re.split(r'\n+', full_generation)
        
        for line in lines:
            line = line.strip()
            # Match lines starting with bullets (- or * or •) or numbers (1., 2., etc.)
            match = re.match(r'^[-*•\d\.\s]+(.*)', line)
            if match:
                starter = match.group(1).strip()
                # Ensure starter is a reasonable question and not duplicate
                if starter and len(starter) > 15 and (starter.endswith('?') or starter.endswith('.')):
                    # Deduplicate
                    if starter not in starters:
                        starters.append(starter)
        return starters

    def _generate_fallback(self, themes: List[str], interests: str, num_starters: int) -> List[str]:
        """
        Fills templates dynamically based on extracted themes and user interests.

        Args:
            themes (List[str]): List of themes.
            interests (str): Raw user interest comma-separated string.
            num_starters (int): Count of templates to generate.

        Returns:
            List[str]: Substituted template starters.
        """
        logger.info("Executing template-based fallback starter generation.")
        
        # Parse interests from comma-separated string
        parsed_interests = [i.strip() for i in re.split(r'[,\n;]', interests) if i.strip()]
        if not parsed_interests:
            parsed_interests = ["networking"]
            
        theme = themes[0] if themes else "innovation"
        interest = parsed_interests[0]
        
        starters = []
        
        # Create unique starters using templates
        for i, template in enumerate(FALLBACK_TEMPLATES):
            t_val = themes[i % len(themes)] if themes else theme
            i_val = parsed_interests[i % len(parsed_interests)]
            
            starter = template.format(theme=t_val, interest=i_val)
            starters.append(starter)
            if len(starters) >= num_starters:
                break
                
        # Hard coded backups in case of formatting errors
        while len(starters) < num_starters:
            starters.append("What trends in your field are you most excited about right now?")
            
        return starters[:num_starters]
