# from dependency_injector.wiring import Provide
#
# from bases import base_qdrant_client
# from di_containers import client_container
# from rag_states import start_and_final_states
#
#
# def get_context_from_qdrant(
#     state: rag_node_states_dto.InputPrompt,
#     qdrant_client: base_qdrant_client.BaseQdrantClient = Provide[client_container.ClientContainer.qdrant_client],
# ) -> rag_node_states_dto.SimpleAnswer:
#     """
#     Get qdrant data from the collections based on user's input
#     :param state: current state
#     :param qdrant_client: qdrant client
#     :return: enhanced prompt
#     """