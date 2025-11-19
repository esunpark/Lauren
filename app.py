from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy

from services.translator import translator

BASE_DIR = Path(__file__).parent

def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'market.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "change-me-in-production"
    db.init_app(app)

    register_cli(app)
    register_routes(app)
    return app


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    language = db.Column(db.String(5), default="en")
    bio = db.Column(db.Text, default="")

    listings = db.relationship("Item", backref="seller", lazy=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<User {self.username}>"


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), default="available")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_available(self) -> bool:
        return self.status == "available"


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="chatting")

    item = db.relationship("Item", backref=db.backref("purchases", lazy=True))
    buyer = db.relationship("User", foreign_keys=[buyer_id])

    def participants(self) -> list[User]:
        return [self.buyer, self.item.seller]


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey("purchase.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    purchase = db.relationship("Purchase", backref=db.backref("messages", lazy=True, order_by="Message.created_at"))
    sender = db.relationship("User")


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db() -> None:
        db.create_all()
        print("Database initialized at", BASE_DIR / "market.db")

    @app.cli.command("seed-demo")
    def seed_demo() -> None:
        db.create_all()
        if User.query.count() > 0:
            print("Database already seeded")
            return
        alice = User(username="alice", language="en", bio="Vintage collector")
        bob = User(username="bob", language="ko", bio="레고 애호가")
        carla = User(username="carla", language="es", bio="Me encantan los sets raros")
        db.session.add_all([alice, bob, carla])
        db.session.flush()
        items = [
            Item(title="Space Cruiser 924", description="Complete set with box", price=250.0, seller=alice),
            Item(title="Forestmen's Hideout", description="Used but complete", price=180.0, seller=bob),
        ]
        db.session.add_all(items)
        db.session.commit()
        print("Seed data created. Users: alice, bob, carla")


def register_routes(app: Flask) -> None:
    @app.context_processor
    def inject_globals() -> dict:
        return {
            "current_user": get_current_user(),
            "supported_languages": SUPPORTED_LANGUAGES,
        }

    @app.route("/")
    def home():
        latest_items = Item.query.order_by(Item.created_at.desc()).limit(5).all()
        latest_purchases = Purchase.query.order_by(Purchase.created_at.desc()).limit(5).all()
        return render_template("home.html", latest_items=latest_items, latest_purchases=latest_purchases)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            language = request.form.get("language") or "en"
            bio = request.form.get("bio", "").strip()
            if not username:
                flash("사용자 이름은 필수입니다.", "danger")
                return redirect(url_for("register"))
            if User.query.filter_by(username=username).first():
                flash("이미 존재하는 이름입니다.", "danger")
                return redirect(url_for("register"))
            user = User(username=username, language=language, bio=bio)
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            flash("환영합니다!", "success")
            return redirect(url_for("items"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            user_id = request.form.get("user_id")
            user = User.query.get(user_id)
            if not user:
                flash("사용자를 찾을 수 없습니다.", "danger")
            else:
                session["user_id"] = user.id
                flash("로그인되었습니다.", "success")
                return redirect(url_for("items"))
        users = User.query.order_by(User.username).all()
        return render_template("login.html", users=users)

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        flash("로그아웃 되었습니다.", "info")
        return redirect(url_for("home"))

    @app.route("/items")
    def items():
        items = Item.query.order_by(Item.created_at.desc()).all()
        return render_template("items/list.html", items=items)

    @app.route("/items/new", methods=["GET", "POST"])
    def new_item():
        user = ensure_login()
        if user is None:
            return redirect(url_for("login"))
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            price = request.form.get("price")
            if not title or not description or not price:
                flash("모든 필드를 채워 주세요.", "danger")
                return redirect(url_for("new_item"))
            item = Item(title=title, description=description, price=float(price), seller=user)
            db.session.add(item)
            db.session.commit()
            flash("상품이 등록되었습니다.", "success")
            return redirect(url_for("items"))
        return render_template("items/new.html")

    @app.route("/items/<int:item_id>")
    def item_detail(item_id: int):
        item = Item.query.get_or_404(item_id)
        purchase = None
        user = get_current_user()
        if user:
            purchase = Purchase.query.filter_by(item_id=item.id, buyer_id=user.id).first()
        return render_template("items/detail.html", item=item, existing_purchase=purchase)

    @app.route("/items/<int:item_id>/start", methods=["POST"])
    def start_purchase(item_id: int):
        user = ensure_login()
        if user is None:
            return redirect(url_for("login"))
        item = Item.query.get_or_404(item_id)
        if item.seller_id == user.id:
            flash("내가 등록한 상품은 구매할 수 없습니다.", "warning")
            return redirect(url_for("item_detail", item_id=item.id))
        purchase = Purchase.query.filter_by(item_id=item.id, buyer_id=user.id).first()
        if purchase:
            flash("이미 채팅을 시작했습니다.", "info")
            return redirect(url_for("purchase_detail", purchase_id=purchase.id))
        if not item.is_available():
            flash("이미 판매된 상품입니다.", "danger")
            return redirect(url_for("items"))
        purchase = Purchase(item=item, buyer=user)
        db.session.add(purchase)
        item.status = "negotiating"
        db.session.commit()
        flash("구매 채팅을 시작했습니다.", "success")
        return redirect(url_for("purchase_detail", purchase_id=purchase.id))

    @app.route("/purchases/<int:purchase_id>")
    def purchase_detail(purchase_id: int):
        user = ensure_login()
        if user is None:
            return redirect(url_for("login"))
        purchase = Purchase.query.get_or_404(purchase_id)
        if user.id not in [purchase.item.seller_id, purchase.buyer_id]:
            flash("접근 권한이 없습니다.", "danger")
            return redirect(url_for("items"))
        translated_messages = [
            translator.translate(msg.body, msg.sender.language, user.language)
            for msg in purchase.messages
        ]
        message_data = list(zip(purchase.messages, translated_messages))
        return render_template(
            "purchases/detail.html",
            purchase=purchase,
            message_data=message_data,
        )

    @app.route("/purchases/<int:purchase_id>/message", methods=["POST"])
    def send_message(purchase_id: int):
        user = ensure_login()
        if user is None:
            return redirect(url_for("login"))
        purchase = Purchase.query.get_or_404(purchase_id)
        if user.id not in [purchase.item.seller_id, purchase.buyer_id]:
            flash("접근 권한이 없습니다.", "danger")
            return redirect(url_for("items"))
        body = request.form.get("body", "").strip()
        if not body:
            flash("메시지를 입력해 주세요.", "warning")
            return redirect(url_for("purchase_detail", purchase_id=purchase.id))
        message = Message(purchase=purchase, sender=user, body=body)
        db.session.add(message)
        db.session.commit()
        flash("메시지가 전송되었습니다.", "success")
        return redirect(url_for("purchase_detail", purchase_id=purchase.id))

    @app.route("/purchases/<int:purchase_id>/complete", methods=["POST"])
    def complete_purchase(purchase_id: int):
        user = ensure_login()
        if user is None:
            return redirect(url_for("login"))
        purchase = Purchase.query.get_or_404(purchase_id)
        if purchase.item.seller_id != user.id:
            flash("판매자만 거래를 완료할 수 있습니다.", "danger")
            return redirect(url_for("purchase_detail", purchase_id=purchase.id))
        purchase.status = "completed"
        purchase.item.status = "sold"
        db.session.commit()
        flash("거래가 완료되었습니다.", "success")
        return redirect(url_for("items"))


def get_current_user() -> Optional[User]:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def ensure_login() -> Optional[User]:
    user = get_current_user()
    if not user:
        flash("로그인이 필요합니다.", "danger")
        return None
    return user


SUPPORTED_LANGUAGES = {
    "en": "English",
    "ko": "한국어",
    "es": "Español",
    "ja": "日本語",
}


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
