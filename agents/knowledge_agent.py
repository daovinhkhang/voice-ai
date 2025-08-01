#!/usr/bin/env python3
"""
Knowledge Base Agent - Tư vấn từ tài liệu
Hỗ trợ upload file PDF, DOCX, TXT, MD và tư vấn dựa trên nội dung
"""

import os
import logging
import tempfile
from typing import List, Dict, Optional
from pathlib import Path

# LangChain imports
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import (
    PyPDFLoader, 
    Docx2txtLoader, 
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Document processing
import pypdf
from docx import Document
import markdown

from config import config

logger = logging.getLogger(__name__)

class KnowledgeBaseAgent:
    """Agent tư vấn dựa trên tài liệu được upload"""
    
    def __init__(self):
        """Khởi tạo Knowledge Base Agent"""
        self.embeddings = OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)
        self.llm = ChatOpenAI(
            model_name=config.LLM_MODEL,
            openai_api_key=config.OPENAI_API_KEY,
            temperature=0.7
        )
        self.vector_store = None
        self.documents = []
        self.knowledge_base_path = "knowledge_base"
        
        # Tạo thư mục knowledge base
        os.makedirs(self.knowledge_base_path, exist_ok=True)
        
        logger.info("Knowledge Base Agent initialized")
    
    def process_document(self, file_path: str, file_type: str) -> bool:
        """
        Xử lý tài liệu và thêm vào knowledge base
        
        Args:
            file_path: Đường dẫn file
            file_type: Loại file (pdf, docx, txt, md)
            
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            logger.info(f"Processing document: {file_path} (type: {file_type})")
            
            # Load document dựa trên loại file
            if file_type.lower() == 'pdf':
                loader = PyPDFLoader(file_path)
            elif file_type.lower() == 'docx':
                loader = Docx2txtLoader(file_path)
            elif file_type.lower() == 'txt':
                loader = TextLoader(file_path, encoding='utf-8')
            elif file_type.lower() == 'md':
                loader = UnstructuredMarkdownLoader(file_path)
            else:
                logger.error(f"Unsupported file type: {file_type}")
                return False
            
            # Load documents
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages/sections")
            
            # Split documents thành chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            splits = text_splitter.split_documents(documents)
            logger.info(f"Split into {len(splits)} chunks")
            
            # Thêm vào vector store
            if self.vector_store is None:
                self.vector_store = Chroma.from_documents(
                    documents=splits,
                    embedding=self.embeddings,
                    persist_directory=self.knowledge_base_path
                )
            else:
                self.vector_store.add_documents(splits)
            
            # Lưu documents
            self.documents.extend(splits)
            
            logger.info(f"Successfully processed document: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return False
    
    def setup_qa_chain(self):
        """Thiết lập QA chain cho tư vấn"""
        if self.vector_store is None:
            logger.warning("No documents loaded. Please upload documents first.")
            return None
        
        # Prompt template cho tư vấn tiếng Việt
        prompt_template = """Bạn là một trợ lý AI chuyên nghiệp, được huấn luyện dựa trên tài liệu của công ty.

Dựa trên các tài liệu được cung cấp, hãy trả lời câu hỏi của người dùng một cách chính xác và hữu ích.

Tài liệu tham khảo:
{context}

Câu hỏi: {question}

Hướng dẫn:
1. Chỉ trả lời dựa trên thông tin có trong tài liệu
2. Nếu không có thông tin trong tài liệu, hãy nói rõ
3. Trả lời bằng tiếng Việt, rõ ràng và dễ hiểu
4. Có thể đưa ra ví dụ hoặc giải thích thêm nếu cần

Trả lời:"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Tạo QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs={"prompt": prompt}
        )
        
        return qa_chain
    
    def get_advice(self, question: str) -> str:
        """
        Lấy tư vấn dựa trên câu hỏi
        
        Args:
            question: Câu hỏi của người dùng
            
        Returns:
            Câu trả lời tư vấn
        """
        try:
            if not self.documents:
                return "Xin lỗi, chưa có tài liệu nào được upload. Vui lòng upload tài liệu trước khi đặt câu hỏi."
            
            qa_chain = self.setup_qa_chain()
            if qa_chain is None:
                return "Không thể thiết lập hệ thống tư vấn. Vui lòng thử lại."
            
            # Lấy câu trả lời
            response = qa_chain.invoke({"query": question})
            
            return response.get("result", "Không thể tìm thấy câu trả lời phù hợp.")
            
        except Exception as e:
            logger.error(f"Error getting advice: {e}")
            return f"Xin lỗi, có lỗi xảy ra: {str(e)}"
    
    def get_document_summary(self) -> Dict:
        """Lấy thông tin tóm tắt về các tài liệu đã upload"""
        if not self.documents:
            return {"message": "Chưa có tài liệu nào được upload"}
        
        summary = {
            "total_documents": len(self.documents),
            "document_types": {},
            "total_chunks": len(self.documents)
        }
        
        # Phân loại theo loại tài liệu
        for doc in self.documents:
            source = doc.metadata.get("source", "unknown")
            file_type = Path(source).suffix.lower()
            summary["document_types"][file_type] = summary["document_types"].get(file_type, 0) + 1
        
        return summary
    
    def clear_knowledge_base(self):
        """Xóa toàn bộ knowledge base"""
        try:
            self.documents = []
            self.vector_store = None
            
            # Xóa thư mục knowledge base
            import shutil
            if os.path.exists(self.knowledge_base_path):
                shutil.rmtree(self.knowledge_base_path)
                os.makedirs(self.knowledge_base_path, exist_ok=True)
            
            logger.info("Knowledge base cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")
            return False 