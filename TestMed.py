# Import necessary libraries
import streamlit as st
from langchain.llms import LlamaCpp
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.base import BaseCallbackHandler
from huggingface_hub import hf_hub_download

#from langchain_community.llms import LlamaCpp
#from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler

# StreamHandler to intercept streaming output from the LLM.
# This makes it appear that the Language Model is "typing"
# in realtime.
class StreamHandler(BaseCallbackHandler):
   def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text
   
   def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

@st.cache_resource
def create_chain(system_prompt):

    # A stream handler to direct streaming output on the chat screen.
    # This will need to be handled somewhat differently.
    # But it demonstrates what potential it carries.
    stream_handler = StreamHandler(st.empty())

    # Callback manager is a way to intercept streaming output from the
    # LLM and take some action on it. Here we are giving it our custom
    # stream handler to make it appear that the LLM is typing the
    # responses in real-time.
    callback_manager = CallbackManager([stream_handler])

    (repo_id, model_file_name) = ("TheBloke/medalpaca-13B-GGUF", "medalpaca-13b.Q4_K_M.gguf")
    model_path = hf_hub_download(repo_id=repo_id, filename=model_file_name, repo_type="model")
    
    # initialize LlamaCpp LLM model
    llm = LlamaCpp(
        model_path=model_path,
        temperature=0.2,
        max_tokens=1024, 
        top_p=1,
        stop=["[INST]"],
        verbose=True,
        streaming=True,
        )

    # Template for structuring user input before converting into a prompt
    template = """
          <s>[INST]{}[/INST]</s>
          [INST]{}[/INST]
          """.format(system_prompt, "{question}")

    # Create a prompt from the template
    prompt = PromptTemplate(template=template, input_variables=["question"])

     # Create an llm chain with LLM and prompt
    llm_chain = prompt | llm
    #llm_chain = LLMChain(llm=llm ,prompt=prompt)

  
    return llm_chain

# Set the webpage title
st.set_page_config(
   page_title="Welcome to MedChat!"
)
   
# Create a header element
st.header("Your own aiChat!")

# Set the system prompt for the chatbot
system_prompt = st.text_area(
  label="System Prompt",
  value="You are a helpful AI assistant who answers questions in short sentences.",
  key="system_prompt")
  
# Create LLM chain for the chatbot
llm_chain = create_chain(system_prompt)


# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = [
         {"role": "assistant", "content": "How may I help you today?"}
    ]
         
if "current_response" not in st.session_state:
    st.session_state.current_response = ""
    
# Loop through each message in the session state and render it
for message in st.session_state.messages:
   with st.chat_message(message["role"]):
      st.markdown(message["content"])


# Take user input from the chat interface
if user_prompt := st.chat_input("Your message here", key="user_input"):
    # Add user input to session state
    st.session_state.messages.append(
         {"role": "user", "content": user_prompt}
    )
    # Pass user input to the LLM chain to generate a response
    response = llm_chain.invoke({"question": user_prompt})   
    print(response)

    # Add LLM response to session state
    st.session_state.messages.append(
         {"role": "assistant", "content": response}
    )        
    # Render LLM response in the chat interface
    with st.chat_message("assistant"):
         st.markdown(response)
    
