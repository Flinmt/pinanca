from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date, datetime

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    cpf: str
    senha_hash: bytes
    imagem_perfil: Optional[str] = None
    data_registro: datetime = Field(default_factory=datetime.utcnow)
    data_ultima_atualizacao: datetime = Field(default_factory=datetime.utcnow)

class Categoria(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_user: int = Field(foreign_key="usuario.id")
    nome: str

class Responsavel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_user: int = Field(foreign_key="usuario.id")
    nome: Optional[str] = None
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")

class OrigemDivida(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_user: int = Field(foreign_key="usuario.id")
    nome: str

class Divida(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="usuario.id")
    id_origem: int = Field(foreign_key="origemdivida.id")
    id_categoria: Optional[int] = Field(default=None, foreign_key="categoria.id")
    id_responsavel: Optional[int] = Field(default=None, foreign_key="responsavel.id")
    data_divida: date
    descricao: Optional[str] = None
    valor_total: float
    parcelas: int
    obs: Optional[str] = None
    pago: bool = False

class DividaParcela(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    divida_id: int = Field(foreign_key="divida.id")
    numero: int
    valor: float
    vence_em: date
    pago: bool = False
    pago_em: Optional[datetime] = None

class EntradaSaida(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="usuario.id")
    id_categoria: Optional[int] = Field(default=None, foreign_key="categoria.id")
    valor: float
    tipo: str   # 'entrada' ou 'saida'
    fixa: bool = False
    periodicidade: str = "nenhuma"  # 'nenhuma','mensal','semanal','anual'
    proxima_execucao: Optional[date] = None
    descricao: Optional[str] = None
    observacao: Optional[str] = None
    ocorrido_em: datetime = Field(default_factory=datetime.utcnow)
    id_parcela: Optional[int] = Field(default=None, foreign_key="dividaparcela.id")
