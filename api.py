from flask import Flask
from flask_restful import Api, reqparse, Resource, fields, marshal_with, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from collections import defaultdict

# Initialize the API and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app)


# Database table for storing transactions
class TransactionModel(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    payer = db.Column(db.String(80), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<Transaction(payer={self.payer}, points={self.points}, timestamp={self.timestamp})>"


# Database table for storing payer balances
class BalanceModel(db.Model):
    __tablename__ = 'payerBalances'

    payer = db.Column(db.String(80), primary_key=True)
    balance = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<PayerBalance(payer={self.payer}, balance={self.balance})>"


# Request parser for the /add endpoint
transaction_args = reqparse.RequestParser()
transaction_args.add_argument('payer', type=str, required=True, help="Payer cannot be blank!")
transaction_args.add_argument('points', type=int, required=True, help="Points cannot be blank!")
transaction_args.add_argument('timestamp', type=str, required=True, help="Timestamp cannot be blank!")

# Fields for marshaling transaction responses
transaction_fields = {
    'id': fields.Integer,
    'payer': fields.String,
    'points': fields.Integer,
    'timestamp': fields.DateTime
}


# Add Transaction Endpoint
class AddTransaction(Resource):
    @marshal_with(transaction_fields)
    def post(self):
        args = transaction_args.parse_args()
        payer = args['payer']
        points = args['points']

        # Parse the provided timestamp
        timestamp = datetime.strptime(args['timestamp'], "%Y-%m-%dT%H:%M:%SZ")

        # Add the transaction to the database
        new_transaction = TransactionModel(payer=payer, points=points, timestamp=timestamp)
        db.session.add(new_transaction)

        # Update or create the payer's balance
        balance_record = BalanceModel.query.filter_by(payer=payer).first()
        if balance_record:
            balance_record.balance += points
        else:
            new_balance = BalanceModel(payer=payer, balance=points)
            db.session.add(new_balance)

        db.session.commit()
        return new_transaction, 200


# Request parser for the /spend endpoint
spend_args = reqparse.RequestParser()
spend_args.add_argument('points', type=int, required=True, help="Points cannot be blank and must be an integer!")


# Spend Points Endpoint
class SpendPoints(Resource):
    def post(self):
        args = spend_args.parse_args()
        points_to_spend = args['points']

        # Fetch all the payer balances and convert to dictionary
        allBalances = BalanceModel.query.all()
        payerBalances = {b.payer: b.balance for b in allBalances}

        # Validate total available balance
        totalBalance = sum([p.balance for p in allBalances])
        if points_to_spend > totalBalance:
            return {"message": "Insufficient points available to spend."}, 400

        # Fetch all transactions sorted by timestamp (oldest first)
        transactions = TransactionModel.query.order_by(TransactionModel.timestamp).all()

        # Get all the transactions with negative points in the beginning
        transactions.sort(key=lambda t: t.points >= 0)

        # Store the balances after processing transactions
        transactionBalances = defaultdict(int)

        # Track the points spend for each payer
        pointsSpent = defaultdict(int)

        # Loop through the transactions
        for transaction in transactions:
            # Add or update the payer's balance
            transactionBalances[transaction.payer] += transaction.points

            # Spend points only if the payer balance is positive, and we have points to spend
            if payerBalances[transaction.payer] > 0 and points_to_spend > 0:
                # Subtract the max possible points we can spend for this payer
                payerBalances[transaction.payer] -= min(points_to_spend, transaction.points)

                # Update the points spent for the payer
                pointsSpent[transaction.payer] += min(points_to_spend, transaction.points)

                # Update the remaining points to spend
                points_to_spend -= min(points_to_spend, transaction.points)
            else:
                continue

        # Update the actual balances in BalanceModel
        for payer, amountSpent in pointsSpent.items():
            # Get the record for this payer
            balance_record = BalanceModel.query.filter_by(payer=payer).first()

            if balance_record:
                # Subtract the amount spent from the original balance
                balance_record.balance -= amountSpent

        db.session.commit()

        # Return the desired response and convert the values to negative
        response = [{"payer": payer, "points": -spent} for payer, spent in pointsSpent.items() if spent > 0]

        return response, 200


# Fields for marshaling balance responses
balance_fields = {
    'payer': fields.String,
    'balance': fields.Integer
}


# Balance Endpoint
class Balance(Resource):
    def get(self):
        # Get all the balances
        balances = BalanceModel.query.all()

        # Store all the payer names and their balances
        response = {}
        for balance in balances:
            response[balance.payer] = balance.balance
        return response, 200


# Register Resources
api.add_resource(AddTransaction, '/add')
api.add_resource(SpendPoints, '/spend')
api.add_resource(Balance, '/balance')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
